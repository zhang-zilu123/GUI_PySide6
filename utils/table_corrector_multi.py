"""
基于 qwen-vl-max 的多表格纠错脚本
自动处理 MinerU 输出的 Markdown 文件中的所有表格错误
使用精确匹配算法建立表格-图片映射关系
"""

import json
import re
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from openai import OpenAI
from difflib import SequenceMatcher
from config.config import CORRECTION_PROMPT
from utils.model_md_to_json import extract_info_from_md

class TableExtractor:
    """从 HTML 中提取表格的解析器"""

    def extract_all_tables(self, html_content: str) -> List[str]:
        """提取HTML中的所有表格"""
        if not isinstance(html_content, str):
            return []

        try:
            # 使用正则表达式提取所有完整的table标签
            pattern = r"<table[^>]*>.*?</table>"
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            return matches
        except (TypeError, AttributeError) as e:
            print(f"提取表格时出错: {e}")
            return []

class QwenVLMaxClient:
    """qwen-vl-max 模型调用客户端 - OpenAI 兼容模式"""

    def __init__(
            self,
            api_key: str,
            base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def call_model(
            self, prompt: str, image_path: str, retry_count: int = 0
    ) -> Dict[str, Any]:
        """调用qwen-vl-max模型"""
        try:
            # 构造消息体
            image_b64 = self.encode_image(image_path)

            print(f"发送请求到: qwen3-vl-plus (OpenAI兼容模式)")

            completion = self.client.chat.completions.create(
                model="qwen3-vl-plus",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0,
                max_tokens=10000,
                seed=42,
            )

            print(f"响应成功，内容长度: {len(completion.choices[0].message.content)}")

            # 转换为原有格式以保持兼容性
            result = {
                "output": {
                    "choices": [
                        {"message": {"content": completion.choices[0].message.content}}
                    ]
                }
            }

            return result

        except Exception as e:
            error_msg = f"调用模型时发生异常: {str(e)}"
            print(f"异常: {error_msg}")
            return {"error": error_msg, "retry_count": retry_count}

class TableValidator:
    """表格输出质检器"""

    def validate_html_table(self, table_html: str) -> Tuple[bool, List[str]]:
        """验证HTML表格的合法性"""
        errors = []

        # 检查是否只包含一个table标签
        table_count = table_html.count("<table")
        if table_count != 1:
            errors.append(f"应该只包含一个table标签，实际包含{table_count}个")

        # 检查HTML是否合法
        try:
            if not table_html.strip().startswith(
                    "<table"
            ) or not table_html.strip().endswith("</table>"):
                errors.append("HTML表格格式不完整")
        except Exception as e:
            errors.append(f"HTML解析错误: {e}")

        # 检查是否包含多余的文本
        clean_html = re.sub(r"<[^>]+>", "", table_html)
        if "```" in clean_html or "markdown" in clean_html.lower():
            errors.append("输出包含不应有的代码块标记或说明文字")

        return len(errors) == 0, errors

    def extract_amounts(self, table_html: str) -> List[float]:
        """从表格中提取所有可能的金额数值"""
        amounts = []
        # 匹配金额格式：支持千分位逗号，1-4位小数
        amount_pattern = r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,4})?\b"
        matches = re.findall(amount_pattern, table_html)

        for match in matches:
            try:
                # 移除千分位逗号
                clean_amount = match.replace(",", "")
                amount = float(clean_amount)
                # 过滤异常值（避免年份、编号等被误判为金额）
                if 0.01 <= amount <= 1000000:
                    amounts.append(amount)
            except ValueError:
                continue

        return amounts

    def check_sum_consistency(
            self, table_html: str, expected_sum: Optional[float]
    ) -> Tuple[bool, float, str]:
        """检查表格中金额的合计一致性"""
        amounts = self.extract_amounts(table_html)
        calculated_sum = sum(amounts)

        notes = f"检测到{len(amounts)}个金额，计算合计: {calculated_sum:.2f}"

        # 如果没有预期合计，只返回计算结果
        if expected_sum is None:
            return True, calculated_sum, notes + "（无预期合计对比）"

        # 计算差值，允许 0.01 的容差
        delta = abs(calculated_sum - expected_sum)
        is_consistent = delta <= 0.01

        notes += f"，预期合计: {expected_sum:.2f}，差值: {delta:.2f}"

        return is_consistent, calculated_sum, notes

class TableCorrector:
    """统一的表格纠错器 - 支持多文件批量处理"""

    def __init__(self, api_key: str, status_callback=None):
        self.api_key = api_key
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.status_callback = status_callback  # 状态更新回调函数

    def _extract_html_from_block(self, block: Dict) -> Optional[str]:
        """从JSON块中深度搜索并提取HTML内容"""

        def find_html(obj):
            if isinstance(obj, dict):
                if "html" in obj:
                    return obj["html"]
                for value in obj.values():
                    result = find_html(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_html(item)
                    if result:
                        return result
            return None

        return find_html(block)

    def _extract_image_path_from_block(self, block: Dict) -> Optional[str]:
        """从JSON块中深度搜索并提取image_path"""

        def find_image_path(obj):
            if isinstance(obj, dict):
                if "image_path" in obj:
                    return obj["image_path"]
                for value in obj.values():
                    result = find_image_path(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_image_path(item)
                    if result:
                        return result
            return None

        return find_image_path(block)

    def _calculate_html_similarity(self, html1: str, html2: str) -> float:
        """计算两个HTML字符串的相似度"""

        # 标准化处理：移除多余空格、统一标点
        def normalize_html(html):
            # 移除多余空格
            html = re.sub(r"\s+", " ", html)
            # 统一中英文标点
            html = html.replace("：", ":")
            html = html.replace("，", ",")
            # 移除HTML标签间的空格
            html = re.sub(r">\s+<", "><", html)
            return html.strip().lower()

        norm_html1 = normalize_html(html1)
        norm_html2 = normalize_html(html2)

        # 使用SequenceMatcher计算相似度
        matcher = SequenceMatcher(None, norm_html1, norm_html2)
        return matcher.ratio()

    def _create_table_image_mapping(
            self, md_tables: List[str], json_data: dict, images_dir: Path
    ) -> Dict[int, str]:
        """使用相似度匹配创建表格-图片映射"""
        print("开始创建表格-图片映射...")

        # 1. 从JSON提取所有表格信息
        json_tables = []  # [(html_content, image_path), ...]

        for page in json_data.get("pdf_info", []):
            # 检查 preproc_blocks
            for block in page.get("preproc_blocks", []):
                if block.get("type") == "table":
                    html_content = self._extract_html_from_block(block)
                    image_filename = self._extract_image_path_from_block(block)

                    if html_content and image_filename:
                        full_image_path = str(images_dir / image_filename)
                        # 验证图片文件存在
                        if Path(full_image_path).exists():
                            json_tables.append((html_content, full_image_path))
                            print(f"  发现JSON表格: {image_filename}")

            # 检查 para_blocks
            for block in page.get("para_blocks", []):
                if block.get("type") == "table":
                    html_content = self._extract_html_from_block(block)
                    image_filename = self._extract_image_path_from_block(block)

                    if html_content and image_filename:
                        full_image_path = str(images_dir / image_filename)
                        if Path(full_image_path).exists():
                            json_tables.append((html_content, full_image_path))
                            print(f"  发现JSON表格: {image_filename}")

        print(f"从JSON提取到 {len(json_tables)} 个表格")

        # 准备回退图片（第一张图片）
        fallback_image = None
        if images_dir.exists():
            for img_file in images_dir.glob("*.jpg"):
                fallback_image = str(img_file)
                break
            if not fallback_image:
                for img_file in images_dir.glob("*.png"):
                    fallback_image = str(img_file)
                    break

        # 2. 为每个MD表格找到最相似的JSON表格
        mapping = {}
        similarity_threshold = 0.9  # 90%相似度阈值

        for i, md_table in enumerate(md_tables):
            best_match = None
            best_similarity = 0.0

            # 计算与所有JSON表格的相似度
            for json_html, json_image_path in json_tables:
                similarity = self._calculate_html_similarity(md_table, json_html)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = json_image_path

            # 根据相似度决定映射
            if best_similarity >= similarity_threshold and best_match:
                mapping[i] = best_match
                print(
                    f"  表格 {i} 相似度匹配成功: {best_similarity:.3f} -> {Path(best_match).name}"
                )
            else:
                mapping[i] = fallback_image
                if best_similarity > 0:
                    print(
                        f"  表格 {i} 相似度不足({best_similarity:.3f}), 使用回退图片: {Path(fallback_image).name if fallback_image else 'None'}"
                    )
                else:
                    print(
                        f"  表格 {i} 无匹配, 使用回退图片: {Path(fallback_image).name if fallback_image else 'None'}"
                    )

        print(f"建立映射完成: {len(mapping)} 个表格")
        return mapping

    def _extract_expected_sum(self, markdown_content: str) -> Optional[float]:
        """从markdown内容中提取预期的合计金额"""
        if not isinstance(markdown_content, str):
            return None

        # 多种合计表达方式的正则模式
        patterns = [
            r"合计[^:：]*[:：]\s*([0-9,]+\.?\d*)",
            r"LUMP\s+SUM[^:：]*[:：]\s*([0-9,]+\.?\d*)",
            r"总计[^:：]*[:：]\s*([0-9,]+\.?\d*)",
            r"Total[^:：]*[:：]\s*([0-9,]+\.?\d*)",
        ]

        for pattern in patterns:
            try:
                match = re.search(pattern, markdown_content, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(",", "")
                    return float(amount_str)
            except (ValueError, AttributeError, TypeError):
                continue

        return None

    def _create_prompt(self, table_html: str, expected_sum: Optional[float]) -> str:
        """构造发送给模型的提示词"""
        prompt = CORRECTION_PROMPT

        # 添加预期合计信息（如果存在）
        if expected_sum:
            prompt += f"\n\n## 重要参考信息：\n预期金额合计：{expected_sum:.2f}（请确保纠错后的表格金额合计与此值一致）"

        # 添加待处理的表格内容
        prompt += f"""

## 待修复的OCR识别结果：
<table_ocr>
{table_html}
</table_ocr>

请严格按照上述要求，仅输出纠错后的HTML表格代码："""

        # print("--------------------------------","\n\n",prompt)

        return prompt

    def _parse_model_response(self, response: Dict) -> Optional[str]:
        """解析模型响应，处理数组格式和Markdown清理"""
        try:
            content_data = response["output"]["choices"][0]["message"]["content"]

            # 处理 qwen-vl-max 的数组格式 content
            if isinstance(content_data, list):
                text_parts = []
                for item in content_data:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                model_output = "\n".join(text_parts)
            elif isinstance(content_data, str):
                model_output = content_data
            else:
                return None

            # 清理 Markdown 代码块标记
            if "```html" in model_output:
                model_output = model_output.replace("```html", "").replace("```", "")

            cleaned_output = model_output.strip()

            # 提取表格HTML
            extractor = TableExtractor()
            tables = extractor.extract_all_tables(cleaned_output)
            return tables[0] if tables else None

        except (KeyError, IndexError, TypeError):
            return None

    def _process_single_table(
            self,
            table_html: str,
            table_index: int,
            image_path: str,
            expected_sum: Optional[float],
    ) -> Dict[str, Any]:
        """处理单个表格"""
        table_report = {
            "table_index": table_index,
            "success": False,
            "had_retry": False,
            "html_valid": False,
            "sum_check_pass": False,
            "calculated_sum": 0.0,
            "expected_sum": expected_sum,
            "notes": "",
            "errors": [],
            "timing": {},
            "original_table": (
                table_html[:200] + "..." if len(table_html) > 200 else table_html
            ),
        }

        # 创建独立的组件实例
        client = QwenVLMaxClient(self.api_key)
        validator = TableValidator()

        try:
            # 发送状态更新
            if self.status_callback:
                self.status_callback(f"正在纠正表格 {table_index + 1}...")

            # 构造提示词
            prompt = self._create_prompt(table_html, expected_sum)

            # 调用模型
            model_start = time.time()
            response = client.call_model(prompt, image_path)
            table_report["timing"]["model_call"] = time.time() - model_start

            if "error" in response:
                table_report["errors"].append(f"模型调用失败: {response['error']}")
                return table_report

            # 解析模型响应
            corrected_table = self._parse_model_response(response)

            # 如果第一次失败，尝试重试
            if not corrected_table:
                print(f"表格 {table_index + 1} 第一次处理失败，尝试重试...")
                retry_prompt = (
                        prompt
                        + "\n\n上次输出包含了额外内容，请严格只输出一个 <table>...</table>，不要任何解释："
                )
                retry_response = client.call_model(
                    retry_prompt, image_path, retry_count=1
                )
                table_report["had_retry"] = True

                if "error" not in retry_response:
                    corrected_table = self._parse_model_response(retry_response)

            if not corrected_table:
                table_report["errors"].append("模型未返回有效的表格")
                return table_report

            # 验证输出
            validation_start = time.time()
            html_valid, validation_errors = validator.validate_html_table(
                corrected_table
            )
            table_report["html_valid"] = html_valid

            if validation_errors:
                table_report["errors"].extend(validation_errors)

            # 检查合计一致性
            sum_consistent, calculated_sum, sum_notes = validator.check_sum_consistency(
                corrected_table, expected_sum
            )
            table_report["sum_check_pass"] = sum_consistent
            table_report["calculated_sum"] = calculated_sum
            table_report["notes"] = sum_notes

            table_report["timing"]["validation"] = time.time() - validation_start

            # 只要返回了有效的HTML表格就算成功
            if html_valid:
                table_report["success"] = True
                table_report["corrected_table"] = corrected_table
                print(f"表格 {table_index + 1} 处理成功")
            else:
                # 即使验证有警告，只要有纠错结果也标记为成功
                if corrected_table:
                    table_report["success"] = True
                    table_report["corrected_table"] = corrected_table
                    print(f"表格 {table_index + 1} 处理成功（有验证警告）")
                else:
                    print(f"表格 {table_index + 1} 处理失败：未获得有效表格")

        except Exception as e:
            table_report["errors"].append(f"处理表格时出现异常: {e}")

        return table_report

    def _extract_info_async(self, corrected_file: str) -> List[Dict]:
        """异步提取结构化数据"""
        try:
            # 发送状态更新
            if self.status_callback:
                file_name = Path(corrected_file).stem
                self.status_callback(f"正在提取结构化数据: {file_name}...")

            temp = extract_info_from_md(corrected_file)
            extracted_info = json.loads(temp).get("费用明细", [])
            print(f"异步提取完成: {corrected_file}, 条数: {len(extracted_info)}")

            # 发送完成状态
            if self.status_callback:
                self.status_callback(f"数据提取完成，共 {len(extracted_info)} 条记录")

            return extracted_info
        except Exception as e:
            print(f"异步提取失败: {corrected_file}, 错误: {e}")
            if self.status_callback:
                self.status_callback(f"数据提取失败: {str(e)}")
            return []

    def _process_single_folder(self, folder_path: Path) -> Dict[str, Any]:
        """同步处理单个票据文件夹"""
        folder_name = folder_path.name
        auto_dir = folder_path / "auto"

        report = {
            "folder_name": folder_name,
            "folder_path": str(folder_path),
            "success": False,
            "table_count": 0,
            "tables_processed": 0,
            "tables_success": 0,
            "table_reports": [],
            "overall_errors": [],
            "timing": {},
            "model_version": "qwen-vl-max",
            "extracted_info": [],
        }

        start_time = time.time()

        try:
            print(f"\n=== 处理文件夹: {folder_name} ===")

            # 查找文件
            md_files = [
                f for f in auto_dir.glob("*.md") if not f.name.endswith(".corrected.md")
            ]
            json_files = list(auto_dir.glob("*_middle.json"))
            images_dir = auto_dir / "images"

            if not md_files:
                report["overall_errors"].append("未找到Markdown文件")
                return report

            if not json_files:
                report["overall_errors"].append("未找到JSON文件")
                return report

            if not images_dir.exists():
                report["overall_errors"].append("未找到图片目录")
                return report

            # 读取文件
            md_file = md_files[0]
            json_file = json_files[0]

            print(f"MD文件: {md_file.name}")
            print(f"JSON文件: {json_file.name}")

            with open(md_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            with open(json_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # 提取所有表格
            extractor = TableExtractor()
            all_tables = extractor.extract_all_tables(markdown_content)

            if not all_tables:
                report["overall_errors"].append("未找到表格")
                print("未找到表格，但仍尝试从原始MD文件提取结构化数据...")
                try:
                    extracted_info = self._extract_info_async(str(md_file))
                    report["extracted_info"].extend(extracted_info)
                    # 如果成功提取到数据，也算作处理成功
                    if extracted_info:
                        report["success"] = True
                        report["output_file"] = str(md_file)  # 使用原始文件
                        print(f"从原始MD文件提取到 {len(extracted_info)} 条结构化数据")
                    else:
                        print("未能从原始MD文件提取到结构化数据")
                except Exception as e:
                    print(f"从原始MD文件提取结构化数据失败: {e}")
                    report["overall_errors"].append(f"提取结构化数据失败: {e}")
                return report

            report["table_count"] = len(all_tables)
            print(f"发现 {len(all_tables)} 个表格")

            # 创建表格-图片映射
            table_image_mapping = self._create_table_image_mapping(
                all_tables, json_data, images_dir
            )

            if not table_image_mapping:
                report["overall_errors"].append("创建表格-图片映射失败")
                print("创建表格-图片映射失败")
                return report

            # 提取预期合计
            expected_sum = self._extract_expected_sum(markdown_content)
            if expected_sum:
                print(f"检测到预期合计: {expected_sum}")

            report["timing"]["preparation"] = time.time() - start_time

            # 处理每个表格
            updated_markdown = markdown_content
            for i, table_html in enumerate(all_tables):
                print(f"\n--- 处理第 {i + 1}/{len(all_tables)} 个表格 ---")

                # 发送处理进度
                if self.status_callback:
                    self.status_callback(f"正在处理表格 {i + 1}/{len(all_tables)}...")

                image_path = table_image_mapping.get(i)
                if not image_path:
                    print(f"表格 {i} 未找到对应图片，跳过")
                    continue

                print(f"使用图片: {Path(image_path).name}")
                table_report = self._process_single_table(
                    table_html, i, image_path, expected_sum
                )
                report["table_reports"].append(table_report)
                report["tables_processed"] += 1

                if table_report["success"]:
                    report["tables_success"] += 1
                    # 替换原表格为纠错后的表格
                    updated_markdown = updated_markdown.replace(
                        table_html, table_report["corrected_table"], 1
                    )

            # 写入纠错后的文件
            if report["tables_success"] > 0:
                if self.status_callback:
                    self.status_callback(f"正在生成纠错文件...")

                corrected_file = auto_dir / f"{md_file.stem}.corrected.md"
                with open(corrected_file, "w", encoding="utf-8") as f:
                    f.write(updated_markdown)

                report["success"] = True
                report["output_file"] = str(corrected_file)
                print(f"已生成纠错文件: {corrected_file.name}")

                # 同步提取结构化数据（这里会调用大模型，可能耗时较长）
                if self.status_callback:
                    self.status_callback(f"正在大模型提取结构化数据，请稍候...")

                extracted_info = self._extract_info_async(str(corrected_file))
                report["extracted_info"].extend(extracted_info)

            # 生成汇总统计
            total_calculated_sum = sum(
                tr.get("calculated_sum", 0) for tr in report["table_reports"]
            )

            report["summary"] = {
                "total_tables": len(all_tables),
                "successful_tables": report["tables_success"],
                "failed_tables": len(all_tables) - report["tables_success"],
                "total_calculated_sum": total_calculated_sum,
                "expected_sum": expected_sum,
                "sum_difference": (
                    abs(total_calculated_sum - expected_sum) if expected_sum else None
                ),
            }

        except Exception as e:
            report["overall_errors"].append(f"处理过程中出现异常: {e}")
            print(f"处理异常: {e}")

        report["timing"]["total"] = time.time() - start_time
        return report

    def process_directory(self, output_dir: Path) -> Dict[str, Any]:
        """异步处理整个输出目录"""
        results = {
            "processed_folders": [],
            "success_count": 0,
            "error_count": 0,
            "total_tables": 0,
            "successful_tables": 0,
            "total_time": 0,
            "info_dict": {},
        }

        start_time = time.time()
        print(f"开始批量处理目录: {output_dir}")
        # 使用线程池并行处理子目录
        futures = []
        with ThreadPoolExecutor(max_workers=4) as executor:  # 设置最大并行线程数
            for subdir in output_dir.iterdir():
                if not subdir.is_dir():
                    continue
                # 跳过非票据目录
                auto_dir = subdir / "auto"
                if not auto_dir.exists():
                    continue

                # 提交异步任务
                futures.append(executor.submit(self._process_single_folder, subdir))

            # 收集结果
            for future in as_completed(futures):
                folder_report = future.result()
                results["processed_folders"].append(folder_report)

                # 统计
                results["total_tables"] += folder_report.get("table_count", 0)
                results["successful_tables"] += folder_report.get("tables_success", 0)

                if folder_report["success"]:
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1

                # 合并提取的结构化数据
                if "extracted_info" in folder_report:
                    results["info_dict"][folder_report["folder_name"]] = folder_report[
                        "extracted_info"
                    ]

        results["total_time"] = time.time() - start_time

        print(f"\n=== 批量处理完成 ===")
        print(f"总文件夹数: {len(results['processed_folders'])}")
        print(f"成功: {results['success_count']}")
        print(f"失败: {results['error_count']}")
        print(f"总表格数: {results['total_tables']}")
        print(f"成功表格数: {results['successful_tables']}")
        print(f"总耗时: {results['total_time']:.2f}秒")

        return results

def main():
    """主函数"""
    # 配置
    from dotenv import load_dotenv

    load_dotenv()
    import os

    API_KEY = os.getenv("DASHSCOPE_API_KEY1")
    current_dir = Path(__file__).resolve().parents[1]
    OUTPUT_DIR = current_dir / "output"
    # OUTPUT_DIR = Path("output")  # MinerU输出目录

    if not OUTPUT_DIR.exists():
        print(f"输出目录 {OUTPUT_DIR} 不存在")
        return

    if API_KEY == "your-api-key-here":
        print("请先设置正确的API密钥")
        return

    # 创建纠错器
    corrector = TableCorrector(API_KEY)

    # 处理所有文件
    results = corrector.process_directory(OUTPUT_DIR)
    print("results", results)

    # 保存总体报告
    # summary_file = OUTPUT_DIR / "correction_summary_multi.json"
    # with open(summary_file, 'w', encoding='utf-8') as f:
    #     json.dump(results, f, ensure_ascii=False, indent=2)
    #
    # print(f"详细报告已保存到: {summary_file}")

if __name__ == "__main__":
    main()
