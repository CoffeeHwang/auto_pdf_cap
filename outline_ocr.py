import requests
import uuid
import time
import json
import re
import os
from pathlib import Path


def run_ocr(secret_key: str, api_url: str, image_files: list) -> list:
    secret_key = secret_key
    api_url = api_url
    image_files = image_files

    headers = {
        'X-OCR-SECRET': secret_key,
    }

    ocr_lines: list = []

    # 처리 이미지 파일 개수만큼 순회
    for i, image_file in enumerate(image_files):

        print(f'OCR처리중 ({i+1}/{len(image_files)}) - "{image_file}"')

        # CLOVA 요청 가이드 형식에 따름
        # 참조 : https://api.ncloud-docs.com/docs/ai-application-service-ocr-example01
        request_json = {
            'version': 'V2',
            'requestId': str(uuid.uuid4()),
            'timestamp': int(round(time.time() * 1000)),
            'lang': 'ko',
            'images': [
                {
                    'format': 'png',
                    'name': 'demo',
                }
            ],
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}

        # files 라고는 하나 2개 이상의 파일을 처리하지 못하는 것으로 보인다.
        files = [
            ('file', open(image_file, 'rb')),
        ]

        response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
        ocr_result = response.json()

        # print(json.dumps(ocr_result, indent=2))

        # 응답값 ocr_result['images'] 가 배열로 들어온다고 가이드 되어 있지만,
        # 하나의 값만 들어오고 배열로 들어오는 경우는 없는듯 하다.
        for image in ocr_result['images']:
            # noinspection PyRedeclaration
            line_start = True
            # noinspection PyRedeclaration
            line = ''
            for field in image['fields']:
                text: str = field['inferText']  # 추출된 글자
                line_break: bool = field['lineBreak']  # 라인끝 여부

                # 텍스트 포맷팅 설정
                # 필드값이 페이지값인지 여부에 따라 접두어로 \t를 붙인다.
                prefix = '\t' if (not line_start and
                                  line_break and
                                  ( text.isdigit() or ( text[:-1].isdigit() and text.endswith('p') ) )
                                  ) \
                              else ' ' if not line_start \
                              else ''

                line += f'{prefix}{text}'

                # 다음 라인 처리 설정
                line_start = line_break

                # 라인끝 처리
                if line_break:
                    ocr_lines.append(line)
                    line = ''
    print(f'OCR처리완료! 총 {len(image_files)}건 \n\n')
    return ocr_lines


def _get_chapter_pattern_index(chapter_patterns: list, text: str):
    for pattern in chapter_patterns:
        if re.match(pattern, text, re.IGNORECASE):  # re.IGNORECASE - 대소문자 무시
            return chapter_patterns.index(pattern)
    return -1


def apply_indentation(input_lines: list) -> list:

    # 챕터 구분 패턴
    sub_patterns = [
        # r"^\d+[. -]+\s*(?!\d).*$",  # 1.,        2 가나다,         3. 마바사 ...
        # r"^\d+([.-]\d+){1}[. -]+\s*(?!\d).*$",  # 1.1,       2-1 가나다,       3-1. 마바사 ...
        # r"^\d+([.-]\d+){2}[. -]+\s*(?!\d).*$",  # 1.1.1,     2-1-1 가나다,     3.1-1. 마바사 ...
        # r"^\d+([.-]\d+){3}[. -]+\s*(?!\d).*$",  # 1.1.1.1,   2-1-1-1 가나다,   3.1-1-1. 마바사 ...
        # r"^\d+([.-]\d+){4}[. -]+\s*(?!\d).*$",  # 1.1.1.1.1, 2-1-1-1-1 가나다, 3.1-1-1-1. 마바사 ...
        r"^\d+[. -]+\s*(?!\d).*$",                # 1.,        2 가나다,         3. 마바사 ...
        r"^\d+([.-]\d+){1}(?![.-]\d)\.?[ ]?.*$",  # 1.1,       2-1 가나다,       3-1. 마바사 ...
        r"^\d+([.-]\d+){2}(?![.-]\d)\.?[ ]?.*$",  # 1.1.1,     2-1-1 가나다,     3.1-1. 마바사 ...
        r"^\d+([.-]\d+){3}(?![.-]\d)\.?[ ]?.*$",  # 1.1.1.1,   2-1-1-1 가나다,   3.1-1-1. 마바사 ...
        r"^\d+([.-]\d+){4}(?![.-]\d)\.?[ ]?.*$",  # 1.1.1.1.1, 2-1-1-1-1 가나다, 3.1-1-1-1. 마바사 ...
        r"^\d+\s*장([. -]+.*)?$",  # 1장, 2장 ...
        r"^\d+\s*부([. -]+.*)?$",  # 1부, 2부 ...
        r"^\d+\s*편([. -]+.*)?$",  # 1편, 2편 ...
        r"^CHAPTER\s*\d+([. -]+.*)?$",  # chapter 1, chapter 2, ...
        r"^LESSON\s*\d+([. -]+.*)?$",  # lesson 1, lesson 2, ...
        r"^PART\s*\d+([. -]+.*)?$",  # part 1, part 2, ...
        r"^PART\s*(I{1,3}|IV|V|VI{0,3}|IX|X)+([. -]+.*)?$",  # part I, part III, part IV ..
    ]

    # 무조건 상위에 있어야 할 패턴
    top_patterns = [
        r"^(APPENDIX|부록|찾아보기|인용|INDEX|후기|마치|EPILOGUE|에필로그|출처)"
    ]

    # 삭제해야 할 패턴
    trash_patterns = [
        r"^\d+$",
        r"^\w+$",
    ]

    cur_depth = -1
    chapter_pattern_list = []
    indented_lines = []

    for line in input_lines:
        # 버리기 패턴이 발견되면 패스
        if _get_chapter_pattern_index(chapter_patterns=trash_patterns, text=line) >= 0:
            continue

        if _get_chapter_pattern_index(chapter_patterns=top_patterns, text=line) >= 0:
            cur_depth = -1
            indent_depth = cur_depth
        else:
            chapter_pattern_index = _get_chapter_pattern_index(chapter_patterns=sub_patterns, text=line)
            if chapter_pattern_index > 0:
                if chapter_pattern_index in chapter_pattern_list:
                    cur_depth = chapter_pattern_list.index(chapter_pattern_index)
                else:
                    chapter_pattern_list.append(chapter_pattern_index)
                    cur_depth += 1
                indent_depth = cur_depth
            else:
                indent_depth = cur_depth + 1

        # indentation = f'{chapter_pattern_index:>2} | {indent_depth:>2} | {"____" * indent_depth}'  # 디버그용
        indentation = "    " * indent_depth
        indented_lines.append(indentation + line)

    return indented_lines


def apply_page_offset(input_lines: list, page_offset: int) -> list:
    """
    페이지넘버가 존재하는 라인인지 검사후 페이지넘버를 오프셋 값만큼 가감한뒤 다시 문자열로 결합한다.
    (이 작업이 필요한 이유 : 가끔 어떤 pdf는 앞표지를 1페이지로 포함하여 1장씩 뒤로 밀리는 경우가 있다.)
    """
    apply_lines = []
    if page_offset == 0:
        return input_lines
    for i, line in enumerate(input_lines):
        if '\t' in line:
            split_fields = line.split('\t')
            title = split_fields[0]
            page = split_fields[-1]
            print(f'title={title}, page={page}')
            apply_lines.append( title + '\t' + str(int(page) + page_offset) )
        else:
            apply_lines.append(line)
    return apply_lines

def apply_none_page(input_lines: list, page_offset: int) -> list:
    """
    # 페이지넘버가 없는 목차에 페이지넘버를 만들어 준다.
    # 만드는 규칙 : 
    리스트를 역순으로 뒤집은뒤 순회한다. 
    순회하면서 이전 목차의 페이지 넘버를 항상 저장해 놓는다.
    - page_offset = 0  : 이전 목차의 페이지 넘버를 그대로 사용
    - page_offset = -1 : 이전 목차의 페이지 넘버에서 1을 뺀값을 사용
    """
    apply_lines = []
    if page_offset > 0:
        # 이전 목차가 다음 목차보다 커지므로 오프셋 값을 0보다 크게 하면 안됨
        return input_lines
    input_lines.reverse()
    save_page = 1
    for i, line in enumerate(input_lines):
        if '\t' in line:
            split_fields = line.split('\t')
            page = split_fields[-1]
            save_page = int(page)
            apply_lines.append(line)
        else:
            page = save_page + page_offset
            save_page = page
            apply_lines.append(line + '\t' + str(page))
    input_lines.reverse()  # 역순으로 뒤집힌 오리지널 리스트를 본래대로 되돌린다.
    apply_lines.reverse()  # 결과 리스트 역시 반환하기 전에 뒤집어 준다.
    return apply_lines


def write_list2file(input_lines: list, filename: str):
    with open(filename, "w") as file:
        for line in input_lines:
            file.write(line + "\n")


def read_file2list(input_file: str) -> list:
    with open(input_file, 'r') as temp_lines:
        return [line.strip() for line in temp_lines]


def get_image_files(path) -> list[str]:
    # 이미지 확장자 목록 정의
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']

    # 이미지 파일 목록을 담을 리스트
    image_files = []

    # 경로 내 파일 확인
    if os.path.isdir(path):
        for file in sorted(os.listdir(path)):
            # 확장자 체크하여 이미지 파일인지 확인
            if Path(file).suffix in image_extensions:
                image_files.append( os.path.join(path,file) )
    return image_files


if __name__ == '__main__':
    ocr_lines = run_ocr(secret_key='dXpzVWpGcmRpeUpuWXlheGhXQ2NBS1dqbFBLZUFWY28=',
                        api_url='https://yi449te0ik.apigw.ntruss.com/custom/v1/35556/bcb66120ed7db6a5b822bd8dcc730dd4b37095eb6e68f6e281ef9cfc1b1acc48/general',
                        image_files=get_image_files("./__OCR 대상파일"))

    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/1. OCR완료파일.txt")

    ocr_lines = apply_indentation(input_lines=ocr_lines)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/2. 목차완성.txt")

    ocr_lines = apply_page_offset(input_lines=ocr_lines, page_offset=1)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/3. 목차완성-오프셋처리.txt")

    ocr_lines = apply_none_page(input_lines=ocr_lines, page_offset=-1)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/4. 목차완성-페이지넘버누락처리.txt")
    for i, line in enumerate(ocr_lines):
        print(f'{i:03}....{line}')


if __name__ == '__test__':
    ocr_lines = read_file2list(input_file="./__OCR 대상파일/1. OCR완료파일.txt")

    ocr_lines = apply_indentation(input_lines=ocr_lines)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/2. 목차완성.txt")

    ocr_lines = apply_page_offset(input_lines=ocr_lines, page_offset=1)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/3. 목차완성-오프셋처리.txt")

    ocr_lines = apply_none_page(input_lines=ocr_lines, page_offset=-1)
    write_list2file(input_lines=ocr_lines, filename="./__OCR 대상파일/4. 목차완성-페이지넘버누락처리.txt")

    for i, line in enumerate(ocr_lines):
        print(f'{i:03}....{line}')
