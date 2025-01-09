"""
주의 :
    PyAutoGUI는 기본 모니터에서만 작동합니다.
    PyAutoGUI는 두 번째 모니터의 화면에서는 신뢰할 수 없습니다
    (마우스 기능은 운영 체제와 버전에 따라 다중 모니터 설정에서 작동할 수도 있고 작동하지 않을 수도 있음).
    https://github.com/asweigart/pyautogui readme 참고

참고 :
    pyautogui.screenshot 해상도 문제(해상도 저하 또는 홀쭉하게 캡쳐 등) 발생시,
    pillow (PIL) 라이브러리 ImageGrab.py 파일에서 아래 코드를 찾아 주석처리 할것
    if bbox:
        im_resized = im.resize((right - left, bottom - top))
        im.close()
        return im_resized

"""

import pyautogui
import os
from PIL import Image
import time
from PyQt5.QtCore import pyqtSignal, pyqtBoundSignal
import subprocess
import sys
from supa_common import *
from typing import Callable


def _screenshot(*, capture_region: tuple, output_dir: str, filename: str, index: int) -> None:
    """화면을 캡쳐하여 파일로 저장한다.

    Args:
        capture_region: 캡쳐할 영역 (x, y, width, height)
        output_dir: 저장할 디렉토리 경로
        filename: 파일명
        index: 파일 인덱스
    """
    output_path = os.path.join(output_dir, f"{filename}_{str(index).zfill(4)}.png")
    # noinspection PyTypeChecker
    pyautogui.screenshot(region=capture_region).save(output_path)


def _getFileListAtPath(*, directory: str, ext: str = "") -> list[str]:
    """특정 경로의 파일 리스트를 반환한다.

    Args:
        directory: 검색할 디렉토리 경로
        ext: 파일 확장자 (빈 문자열이면 모든 파일)

    Returns:
        파일 경로 리스트
    """
    if ext == "":
        filelist = [os.path.join(directory, f) for f in os.listdir(directory) 
                   if os.path.isfile(os.path.join(directory, f))]
    else:
        filelist = [os.path.join(directory, f) for f in os.listdir(directory) 
                   if os.path.isfile(os.path.join(directory, f)) and f.endswith(ext)]
    return sorted(filelist, key=lambda x: x)


def _open_directory(path):
    if sys.platform == "win32":  # Windows
        os.startfile(path)
    elif sys.platform == "darwin":  # macOS
        subprocess.call(['open', path])
    else:  # Linux 및 기타
        subprocess.call(['xdg-open', path])


def _create_pdf(*, output_dir: str, file_name: str, show_log_fn: Callable[[str], None]) -> None:
    """캡쳐된 이미지들을 PDF로 변환한다.

    Args:
        output_dir: 이미지 파일이 있는 디렉토리 경로
        file_name: 생성될 PDF 파일명
        show_log_fn: 로그 출력 함수
    """
    # 이미지 파일 리스트를 가져온다.
    imagepaths = _getFileListAtPath(directory=output_dir, ext='png')

    images = [Image.open(image).convert('RGB') for image in imagepaths]
    show_log_fn("pdf 취합중...")
    
    pdf_path = os.path.join(output_dir, f'{file_name}.pdf')
    images[0].save(pdf_path, save_all=True, append_images=images[1:])

    show_log_fn("pdf 취합완료.")

    # PDF 파일 생성 후 폴더 열기
    _open_directory(output_dir)


def auto_pdf_capture(file_name: str, page_loop: int,
                     x1: int, y1: int, x2: int, y2: int,
                     margin: int = 0, diff_width: int = 0,
                     res: int = 1, automation_delay: float = 0.2,
                     left_first: bool = True,
                     log_message_signal: pyqtSignal | pyqtBoundSignal | None = None,
                     is_running: Callable[[], bool] | None = None) -> bool:
    """
    자동으로 화면을 캡쳐한뒤 pdf를 생성한다.

    Args:
        file_name: 생성될 pdf 파일명
                   '실전에서 바로쓰는 Next.js (박수현 역) - 한빛미디어'  # 책이름(저자 or 역자 or 옮김) - 출판사명
        page_loop : 캡쳐 반복 횟수 (캡쳐 페이지수)
        x1: 캡쳐할 영역의 우상단 x 좌표 (여백을 완전히 배제한, 컨텐츠가 있는 영역만을 판단)
        y1: 캡쳐할 영역의 우상단 y 좌표 (여백을 완전히 배제한, 컨텐츠가 있는 영역만을 판단)
        x2: 캡쳐할 영역의 우하단 x 좌표 (여백을 완전히 배제한, 컨텐츠가 있는 영역만을 판단)
        y2: 캡쳐할 영역의 우하단 y 좌표 (여백을 완전히 배제한, 컨텐츠가 있는 영역만을 판단)
        margin: 마진폭 (컨텐츠 영역에서 확장시킬 여백의 길이값. 마진폭이 0이면 컨텐츠 영역만 캡쳐된다.)
                실제 캡쳐는 마진폭만큼 확장된 영역을 캡쳐한다.
        diff_width: 좌우 인쇄폭 차이 (좌우 인쇄폭 차이가 있으면 pdf를 수직스크롤로 읽을때 페이지
                    연결부가 미묘하게 좌우로 지그재그 인쇄되어 라인일치가 되지 않는 불편이 있다.)
                    좌우 인쇄폭 차이값을 넣어주면 라인을 일치시킨 캡쳐가 진행된다.
        res: 레티나 디스플레이일 경우 2로 설정. 아닐 경우 1로 설정
             pillow 버전업되면서(? 확실친 않음) 무조건 1로 해야 한다.
        automation_delay: 자동화 딜레이 시간(초) 설정. 페이지 로딩할 시간을 일정시간(초) 부여 해준다.
                          (가끔 로딩이 완료 되지 않은 상태에서 캡쳐가 되면 글자가 뭉개지기 때문.)
        left_first: 좌측부터 캡쳐할지 여부. True면 좌측부터, False면 우측부터 캡쳐한다.
        log_message_signal: 로그 메시지를 전달할 신호
        is_running: 캡쳐 중지 여부를 확인할 함수
    Returns:
        bool: 성공여부
    """
    def show_log(log_message: str):
        if log_message_signal:
            log_message_signal.emit(log_message) # type: ignore
        print(log_message)

    x1 -= margin
    y1 -= margin
    x2 += margin
    y2 += margin

    x = x1  # 캡쳐 시작좌표 x
    y = y1  # 캡쳐 시작좌표 y
    width = x2 - x1  # 캡쳐할 영역의 너비
    height = y2 - y1  # 캡쳐할 영역의 높이
    capture_region_first_page = (x * res, y * res, width * res, height * res)
    capture_region_left_page = (x * res, y * res, (width - diff_width) * res, height * res)
    capture_region_right_page = ((x + diff_width) * res, y * res, (width - diff_width) * res, height * res)
    dir_name = f'./__{file_name}'
    # --------------------------------------------------------------------------------

    show_log(f'전체화면 {pyautogui.size()}')
    show_log(f'x = {x}')
    show_log(f'y = {y}')
    show_log(f'width = {width}')
    show_log(f'height = {height}')
    show_log(f'capture_region_first_page = {capture_region_first_page}')
    show_log(f'capture_region_left_page = {capture_region_left_page}')
    show_log(f'capture_region_right_page = {capture_region_right_page}')

    show_log("\n캡쳐 대상으로 포커스를 이동하세요...\n5초뒤 시작합니다.\n")

    # 카운트 다운
    tmp_seconds = 5
    for i in range(tmp_seconds, 0, -1):
        show_log(str(i))
        time.sleep(1)

    # 생성 디렉터리 체크
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # --------------------------------------------------------------------
    # 캡쳐 자동화
    # --------------------------------------------------------------------
    start_time = time.time()

    # 첫 페이지 캡쳐
    capture_region = capture_region_first_page
    show_log(f'\n캡쳐 1 - 표지 {capture_region}')
            
    _screenshot(
        capture_region=capture_region,
        output_dir=dir_name,
        filename=file_name,
        index=1
    )
    pyautogui.press("right")
    time.sleep(automation_delay)

    # 페이지 수 까지 반복 캡쳐 수행
    for i in range(2, page_loop + 1):

        # 중지 요청이 있는지 확인
        if is_running and not is_running():
            show_log("\n캡쳐가 중지되었습니다.")
            _create_pdf(output_dir=dir_name, file_name=file_name, show_log_fn=show_log)
            return False

        # 좌측부터 시작하는 경우와 우측부터 시작하는 경우에 따라 캡쳐 순서를 다르게 처리
        if left_first:
            capture_region = capture_region_left_page if i % 2 == 0 else capture_region_right_page
        else:
            capture_region = capture_region_right_page if i % 2 == 0 else capture_region_left_page
            
        if diff_width > 0:
            which = '좌측 ' if (left_first and i % 2 == 0) or (not left_first and i % 2 != 0) else '우측 '
        else:
            which = ''
        
        show_log(f'캡쳐 {i} - {which}{capture_region}')
        _screenshot(
            capture_region=capture_region,
            output_dir=dir_name,
            filename=file_name,
            index=i
        )
        pyautogui.press("right")
        pyautogui.sleep(automation_delay)  # 페이지 로딩할 시간을 일정시간(초) 부여 해준다. (가끔 로딩이 완료 되지 않은 상태에서 캡쳐가 되면 글자가 뭉개지기 때문.)

    show_log("캡쳐 완료.")
        
    _create_pdf(output_dir=dir_name, file_name=file_name, show_log_fn=show_log)

    show_log('-----------------------------------------------------------')
    show_log(f'총 소요시간: {time.time() - start_time:.2f}초')
    # --------------------------------------------------------------------

    return True

# end of file