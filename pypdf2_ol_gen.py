# --------------------------------------------------------------------
# simple and easy way to generate a PDF outline
# --------------------------------------------------------------------
import os
import PyPDF2

# --------------------------------------------------------------------------------
OUTLINE_FILE = '초보자도 프로처럼 만드는 플러터 앱 개발 (이정주) - 한빛미디어.txt'
PDF_FILE     = '초보자도 프로처럼 만드는 플러터 앱 개발 (이정주) - 한빛미디어.pdf'
# --------------------------------------------------------------------------------

def pdf_outline_gen(pdf_file: str, ol_file: str, depth_sep: str, page_sep: str):
    if depth_sep == page_sep:
        raise Exception('depth_sep and page_sep must be different.')

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
                    raise Exception('The first line must be 0 depth.')

                title = ol_attr[0].replace(depth_sep, '')
                print(f'title = {title}')

                if len(ol_attr) != 2:
                    raise Exception('The line must be 2 items. Check page_sep or page_index')
                else:
                    page = int(ol_attr[1]) - 1
                    if page < bef_page:
                        raise Exception('The current page index should be same or larger than the previous page index.')
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

# end of file