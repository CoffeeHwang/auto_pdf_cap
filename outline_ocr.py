import requests
import uuid
import time
import json
import re
import os
from pathlib import Path
from typing import Callable


def run_ocr(secret_key: str, api_url: str, image_files: list, show_log: Callable[[str], None] = None) -> list:
    secret_key = secret_key
    api_url = api_url
    image_files = image_files

    headers = {
        'X-OCR-SECRET': secret_key,
    }

    ocr_lines: list = []

    # 처리 이미지 파일 개수만큼 순회
    for i, image_file in enumerate(image_files):
        if show_log:
            show_log(f'OCR처리중 ({i+1}/{len(image_files)}) - "{os.path.basename(image_file)}"')
        else:
            print(f'OCR처리중 ({i+1}/{len(image_files)}) - "{os.path.basename(image_file)}"')

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

        try:
            with open(image_file, 'rb') as f:
                files = [
                    ('file', f),
                ]
                response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
                response.raise_for_status()
        except FileNotFoundError:
            if show_log:
                show_log(f"⚠️ 이미지 파일을 찾을 수 없습니다: {image_file}")
            else:
                print(f"⚠️ 이미지 파일을 찾을 수 없습니다: {image_file}")
            continue
        except requests.exceptions.ConnectionError:
            if show_log:
                show_log("⚠️ 네트워크 연결을 확인할 수 없습니다.")
            else:
                print("⚠️ 네트워크 연결을 확인할 수 없습니다.")
            return ocr_lines
        except requests.exceptions.RequestException as e:
            if show_log:
                show_log(f"❌ OCR API 요청 중 오류 발생: {e}")
            else:
                print(f"❌ OCR API 요청 중 오류 발생: {e}")
            return ocr_lines
        
        try:
            ocr_result = response.json()
        except json.JSONDecodeError:
            if show_log:
                show_log("❌ OCR API 응답을 처리할 수 없습니다.")
            else:
                print("❌ OCR API 응답을 처리할 수 없습니다.")
            continue

        # print(json.dumps(ocr_result, indent=2))

        # 응답값 ocr_result['images'] 가 배열로 들어온다고 가이드 되어 있지만,
        # 하나의 값만 들어오고 배열로 들어오는 경우는 없는듯 하다.
        for image in ocr_result['images']:
            # noinspection PyRedeclaration
            line_start = True
            # noinspection PyRedeclaration
            line = ''
            for field in image['fields']:
                text: str = field['inferText'].strip()  # 추출된 글자 (앞뒤 공백 제거)
                line_break: bool = field['lineBreak']  # 라인끝 여부

                # 페이지 번호인지 확인
                # 1. 순수 숫자인 경우
                # 2. 숫자+'p'로 끝나는 경우 (예: "123p")
                # 3. 숫자+'페이지'로 끝나는 경우 (예: "123페이지")
                is_page_number = False
                if text.isdigit():  # 순수 숫자
                    text = int(text)  # "014" 와 같은 경우도 숫자로 변환 : "014" -> 4
                    is_page_number = True
                else:
                    # 'p' 또는 '페이지'로 끝나는 경우 처리
                    for suffix in ['p', '페이지']:
                        if text.endswith(suffix) and text[:-len(suffix)].isdigit():
                            text = text[:-len(suffix)]  # 접미사 제거
                            is_page_number = True
                            break

                # 텍스트 포맷팅 설정
                # 필드값이 페이지값인지 여부에 따라 접두어로 \t를 붙인다.
                if not line_start and line_break and is_page_number:
                    prefix = '\t'
                elif not line_start:
                    prefix = ' '
                else:
                    prefix = ''

                line += f'{prefix}{text}'

                # 다음 라인 처리 설정
                line_start = line_break

                # 라인끝 처리
                if line_break:
                    if line.strip():  # 빈 라인 제외
                        ocr_lines.append(line)
                    line = ''
    if show_log:
        show_log(f'OCR처리완료! 총 {len(image_files)}건 \n\n')
    else:
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
    
    Args:
        input_lines (list): 입력 라인 리스트
        page_offset (int): 페이지 오프셋 값 (+1 또는 -1)
        
    Returns:
        list: 페이지 오프셋이 적용된 라인 리스트
    """
    apply_lines = []
    if page_offset == 0:
        return input_lines
        
    for i, line in enumerate(input_lines):
        if '\t' in line:
            try:
                split_fields = line.split('\t')
                title = split_fields[0]
                page = split_fields[-1].strip()  # 앞뒤 공백 제거
                
                # 페이지 번호를 정수로 변환
                page_num = int(page)
                
                # 오프셋 적용 후 음수가 되지 않도록 처리
                new_page = max(1, page_num + page_offset)
                
                apply_lines.append(f"{title}\t{new_page}")
            except (ValueError, IndexError) as e:
                # 페이지 번호가 숫자가 아니거나, 분리된 필드가 부족한 경우
                apply_lines.append(line)  # 원본 라인 유지
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

# end of file