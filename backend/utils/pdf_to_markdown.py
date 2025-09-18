# 配置 poppler 路径
import os
import sys
import logging
import threading
import io
from pathlib import Path
from .logger import logger_init

logger = logger_init("pdf_to_markdown")

# 尝试从环境变量获取，否则使用默认路径
poppler_path = os.getenv("POPPLER_PATH")
if not poppler_path:
    # 常见安装路径
    possible_paths = [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        r"E:\Programs\poppler-25.07.0\Library\bin"
    ]
    for path in possible_paths:
        if Path(path).exists():
            poppler_path = path
            break

if not poppler_path:
    raise FileNotFoundError(
        "未找到poppler路径，请设置POPPLER_PATH环境变量或安装poppler到默认位置"
    )

# 临时添加到系统路径
os.environ["PATH"] = poppler_path + os.pathsep + os.environ["PATH"]

# 导入必要的库
import fitz  # PyMuPDF
from fitz import open as fitz_open
from unstructured.partition.pdf import partition_pdf
from langchain_unstructured import UnstructuredLoader
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from PIL import Image

def resolve_pdf_path(pdf_path):
    """解析PDF路径，支持相对路径和绝对路径"""
    path = Path(pdf_path)
    
    # 如果只提供了文件名，没有扩展名，添加.pdf扩展名
    if not path.suffix:
        path = path.with_suffix('.pdf')
    
    # 如果是绝对路径，直接返回
    if path.is_absolute():
        return path
    
    # 相对路径，从当前工作目录解析
    return Path.cwd() / path

# 方法1: 使用 langchain_unstructured 加载 PDF
def load_with_langchain(pdf_path):
    logger.info(f"使用 LangChain UnstructuredLoader 加载 PDF: {pdf_path}")
    loader_local = UnstructuredLoader(
        file_path=str(pdf_path),
        strategy="hi_res",  # 高分辨率模式，支持复杂文档
        infer_table_structure=True,  # 自动解析表格结构
        languages=["chi_sim", "eng"],  # 支持中英文 OCR
        ocr_engine="paddleocr",  # 指定 PaddleOCR 作为 OCR 引擎
        poppler_path=poppler_path  # 明确指定 poppler 路径
    )

    docs_local = []
    for doc in loader_local.lazy_load():
        docs_local.append(doc)
    
    logger.info(f"成功加载 {len(docs_local)} 个文档元素")
    return docs_local

# 方法2: 使用 unstructured 直接处理 PDF
def process_with_unstructured(pdf_path):
    logger.info("使用 unstructured 直接处理 PDF...")
    # 提取文本/结构化内容
    elements = partition_pdf(
        filename=str(pdf_path),
        infer_table_structure=True,  # 开启表格结构检测
        strategy="hi_res",  # 高分辨率 OCR, 适合复杂表格
        languages=["chi_sim", "eng"],  # 中英文混合识别
        ocr_engine="paddleocr",  # 指定 PaddleOCR 引擎
        poppler_path=poppler_path  # 明确指定 poppler 路径
    )
    
    logger.info(f"成功提取 {len(elements)} 个文档元素")
    return elements

# 可视化函数
def plot_pdf_with_boxes(pdf_page, segments):
    pix = pdf_page.get_pixmap()
    pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    fig, ax = plt.subplots(1, figsize=(10, 10))
    ax.imshow(pil_image)
    categories = set()
    category_to_color = {
        "Title": "orchid",
        "Image": "forestgreen",
        "Table": "tomato",
    }
    for segment in segments:
        points = segment["coordinates"]["points"]
        layout_width = segment["coordinates"]["layout_width"]
        layout_height = segment["coordinates"]["layout_height"]
        scaled_points = [
            (x * pix.width / layout_width, y * pix.height / layout_height)
            for x, y in points
        ]
        box_color = category_to_color.get(segment["category"], "deepskyblue")
        categories.add(segment["category"])
        rect = patches.Polygon(
            scaled_points, linewidth=1, edgecolor=box_color, facecolor="none"
        )
        ax.add_patch(rect)

    # Make legend
    legend_handles = [patches.Patch(color="deepskyblue", label="Text")]
    for category in ["Title", "Image", "Table"]:
        if category in categories:
            legend_handles.append(
                patches.Patch(color=category_to_color[category], label=category)
            )
    ax.axis("off")
    ax.legend(handles=legend_handles, loc="upper right")
    plt.tight_layout()
    plt.show()

def render_page(pdf_path, doc_list, page_number=None, print_text=True, save_annotated=False):
    """渲染PDF页面并添加标注
    
    参数:
        pdf_path: PDF文件路径
        doc_list: 文档元素列表(包含metadata)
        page_number: 指定页码(None表示所有页面)
        print_text: 是否打印提取的文本
        save_annotated: 是否保存标注版PDF
    """
    # 打开原始PDF文件
    pdf_doc = fitz_open(pdf_path)
    output_doc = None
    
    if save_annotated:
        # 确保输出文件与源文件在同一目录
        pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
        output_path = os.path.join(pdf_dir, f"{Path(pdf_path).stem}_annotated.pdf")
        output_doc = fitz_open()
    
    pages_to_process = [page_number - 1] if page_number else range(len(pdf_doc))
    
    for page_num in pages_to_process:
        pdf_page = pdf_doc.load_page(page_num)
        current_page = page_num + 1
        page_docs = [
            doc for doc in doc_list 
            if doc.metadata.get("page_number") == current_page
        ]
        segments = [doc.metadata for doc in page_docs]
        
        if not save_annotated:
            plot_pdf_with_boxes(pdf_page, segments)
        
        if save_annotated:
            output_page = output_doc.new_page(
                width=pdf_page.rect.width,
                height=pdf_page.rect.height
            )
            output_page.show_pdf_page(output_page.rect, pdf_doc, page_num)
            
            category_to_color = {
                "Title": (0.6, 0.2, 0.8),   # 紫色
                "Image": (0.0, 0.5, 0.0),    # 绿色
                "Table": (1.0, 0.4, 0.4),   # 红色
                "Text": (0.0, 0.7, 1.0)     # 蓝色
            }
            
            for segment in segments:
                points = segment["coordinates"]["points"]
                layout_width = segment["coordinates"]["layout_width"]
                layout_height = segment["coordinates"]["layout_height"]
                scaled_points = [
                    (x * pdf_page.rect.width / layout_width, 
                     y * pdf_page.rect.height / layout_height)
                    for x, y in points
                ]
                
                # 添加标注
                annot = output_page.add_polygon_annot(scaled_points)
                annot.set_colors(
                    stroke=category_to_color.get(segment["category"], (0.0, 0.7, 1.0))
                )
                annot.set_opacity(0.4)
                annot.update()
                
                # 为重要元素添加标签
                if segment["category"] in ["Title", "Table"]:
                    center_x = sum(p[0] for p in scaled_points)/len(scaled_points)
                    center_y = sum(p[1] for p in scaled_points)/len(scaled_points)
                    output_page.insert_text(
                        (center_x, center_y - 10),
                        segment["category"],
                        fontsize=10,
                        color=(0,0,0),
                        rotate=0
                    )
    
    if save_annotated and output_doc:
        output_doc.save(output_path)
        logger.info(f"已保存标注版PDF到: {output_path}")
        return output_path

# 提取图片并转换为 Markdown
def extract_images_and_convert_to_markdown(pdf_path, elements):
    logger.info("提取图片并转换为 Markdown...")
    # 创建输出目录，确保与源文件在同一目录
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    output_dir = os.path.join(pdf_dir, Path(pdf_path).stem)
    os.makedirs(output_dir, exist_ok=True)
    
    # 提取图片并保存
    pdf_doc = fitz_open(pdf_path)
    image_map = {}  # 映射 page_num -> list of image paths

    for page_num, page in enumerate(pdf_doc, start=1):
        image_map[page_num] = []
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(pdf_doc, xref)
            img_path = os.path.join(output_dir, f"page{page_num}_img{img_index}.png")
            if pix.n < 5:  # RGB / Gray
                pix.save(img_path)
            else:  # CMYK 转 RGB
                pix = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), pix)
                pix.save(img_path)
            image_map[page_num].append(img_path)

    # 转换为 Markdown
    md_lines = []
    inserted_images = set()  # 用来记录已经插入过的图片, 避免重复

    for el in elements:
        cat = el.category
        text = el.text
        page_num = el.metadata.page_number

        if cat == "List" and text.strip().startswith("- "):
            md_lines.append(text + "\n")
        elif cat == "Title":
            md_lines.append(f"# {text}\n")
        elif cat in ["Header", "Subheader"]:
            md_lines.append(f"## {text}\n")
        elif cat == "Table":
            if hasattr(el.metadata, "text_as_html") and el.metadata.text_as_html:
                from html2text import HTML2Text
                converter = HTML2Text()
                md_lines.append(converter.handle(el.metadata.text_as_html) + "\n")
            else:
                md_lines.append(el.text + "\n")
        elif cat == "Image":
            # 避免重复插入: 只插入当前图片对应的文件
            for img_path in image_map.get(page_num, []):
                if img_path not in inserted_images:
                    # 使用相对路径，确保在Markdown中正确引用图片
                    rel_img_path = os.path.relpath(img_path, pdf_dir)
                    md_lines.append(f"![Image]({rel_img_path})\n")
                    inserted_images.add(img_path)
        else:
            md_lines.append(text + "\n")

    # 写入 Markdown 文件，确保与源文件在同一目录
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    output_md = os.path.join(pdf_dir, f"{Path(pdf_path).stem}.md")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"转换完成, 已生成: {output_md}")
    logger.info(f"图片文件夹路径: {output_dir}/")

# 处理PDF的主函数
def process_pdf(pdf_path_str):
    """处理PDF文件的主函数"""
    try:
        # 解析PDF路径
        pdf_path = resolve_pdf_path(pdf_path_str)
        logger.info(f"开始处理PDF: {pdf_path}")
        logger.info(f"开始处理 PDF: {pdf_path}\n")
        
        if not pdf_path.exists():
            error_msg = f"PDF文件不存在: {pdf_path}"
            logger.error(error_msg)
            return False
            
        # 尝试方法1
        docs = load_with_langchain(pdf_path)
        # 可视化所有页面并保存标注版
        render_page(pdf_path, docs, save_annotated=True)
        
        # 尝试方法2
        elements = process_with_unstructured(pdf_path)
        # 转换为 Markdown
        extract_images_and_convert_to_markdown(pdf_path, elements)
        
        logger.info(f"PDF处理完成: {pdf_path}")
        return True
    except Exception as e:
        error_msg = f"处理过程中出现错误: {e}"
        logger.error(f"详细错误信息:{error_msg}")
        return False

# 在后台线程中处理PDF
def process_pdf_in_thread(pdf_path_str):
    """在后台线程中处理PDF文件"""
    thread = threading.Thread(target=process_pdf, args=(pdf_path_str,))
    thread.daemon = True  # 设置为守护线程，主程序退出时线程也会退出
    thread.start()
    logger.info(f"已在后台线程启动PDF处理: {pdf_path_str}")
    return thread

# 主函数
def main():
    # 检查命令行参数
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help', '/?']:
        print("PDF转Markdown工具 - 使用说明")
        print("==========================")
        print("功能: 将PDF文件转换为Markdown格式，并生成带批注的PDF")
        print("\n用法: python pdf_to_markdown.py <pdf_path>")
        print("\n参数:")
        print("  <pdf_path>  PDF文件路径，支持相对路径和绝对路径")
        print("  -h, --help  显示此帮助信息")
        print("\n示例:")
        print("  python pdf_to_markdown.py example.pdf")
        print("  python pdf_to_markdown.py /path/to/document.pdf")
        print("  python pdf_to_markdown.py C:\\Documents\\report.pdf")
        print("\n输出:")
        print("  - [文件名].md - Markdown格式的文本内容")
        print("  - [文件名]_annotated.pdf - 带批注的PDF文件")
        print("  - [文件名]/ - 包含提取的图片的目录")
        return
    
    # 获取PDF路径参数
    pdf_path = sys.argv[1]
    
    # 处理PDF
    process_pdf(pdf_path)

if __name__ == "__main__":
    main()