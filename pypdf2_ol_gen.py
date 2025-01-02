# --------------------------------------------------------------------
# simple and easy way to generate a PDF outline
# --------------------------------------------------------------------
import os
import PyPDF2

# --------------------------------------------------------------------------------
OUTLINE_FILE = '초보자도 프로처럼 만드는 플러터 앱 개발 (이정주) - 한빛미디어.txt'
PDF_FILE     = '초보자도 프로처럼 만드는 플러터 앱 개발 (이정주) - 한빛미디어.pdf'
# --------------------------------------------------------------------------------

def pdf_outline_gen(pdf_file: str, ol_file: str, depth_sep: str, page_sep: str) -> tuple[bool, str]:
    if depth_sep == page_sep:
        return False, "depth_sep and page_sep must be different."

    # origin PDF file open
    with open(pdf_file, 'rb') as f_pdf:
        pdf_reader = PyPDF2.PdfReader(f_pdf)
        pdf_writer = PyPDF2.PdfWriter()

        # get original pages (copy for new file)
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            pdf_writer.add_page(page)

        # get outline guide and apply to new file
        with open(ol_file, 'r') as f_ol:
            parent_dic = {}
            bef_page = 0
            for idx, line in enumerate(f_ol):
                ol_attr = line.replace('\n', '').split(page_sep)
                depth_level = ol_attr[0].count(depth_sep)

                if idx == 0 and depth_level != 0:
                    return False, "첫행의 깊이레벨은 0이어야 합니다."

                title = ol_attr[0].replace(depth_sep, '')
                print(f'title = {title}')

                if len(ol_attr) != 2:
                    return False, f"페이지 누락 확인, 제목 : {title}"
                else:
                    # 페이지 번호가 비어있는지 확인
                    if not ol_attr[1].strip():
                        return False, f"페이지 번호가 비어 있습니다. 제목 : {title}"

                    try:
                        page = int(ol_attr[1]) - 1
                    except ValueError:
                        return False, f"잘못된 페이지 번호입니다. 제목 : {title}, 페이지 : {ol_attr[1]}"
                        
                    if bef_page > page :
                        return False, f"페이지가 앞장 보다 작을수 없습니다. 페이지 : {bef_page} > {page} ?"
                    bef_page = page

                print(f'page = {page}\n')

                if depth_level > 0:
                    parent = parent_dic[depth_level - 1]
                else:
                    parent = None

                # print(f'line index = {idx}')
                # print(f'depth_level = {depth_level}')
                # print(f'title = {title}')
                # print(f'page = {page}')
                # print(f'parent = {parent}\n')

                # page index start from 0. so, -1
                parent_dic[depth_level] = pdf_writer.add_outline_item(title, page, parent=parent)

        # 새로운 PDF 파일 작성
        pdf_dir = os.path.dirname(pdf_file)
        pdf_name = os.path.basename(pdf_file)
        with open(os.path.join(pdf_dir, f'_{pdf_name}'), 'wb') as f_pdf_new:
            pdf_writer.write(f_pdf_new)

    # 기존 파일과 새로운 파일 네이밍
    os.rename(pdf_file, os.path.join(pdf_dir, f'_BAK_{pdf_name}'))
    os.rename(os.path.join(pdf_dir, f'_{pdf_name}'), pdf_file)

    return True, "개요가 정상적으로 적용되었습니다."

# end of file