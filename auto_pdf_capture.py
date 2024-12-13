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


def _screenshot(capture_region: tuple, filename: str, index: int):
    # noinspection PyTypeChecker
    pyautogui.screenshot(region=capture_region).save(filename + '_' + str(index).zfill(4) + '.png')


def _getFileListAtPath(path: str, ext: str = None) -> list:
    """특정 경로의 파일 리스트를 반환한다."""
    if ext is None:
        filelist = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    else:
        filelist = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(ext)]
    return sorted(filelist, key=lambda x: x)


def auto_pdf_capture(file_name: str, page_loop: int,
                     x1: int, y1: int, x2:int, y2: int,
                     margin: int = 0, diff_width: int = 0,
                     res: int = 1, automation_delay: float = 0.2 ) -> bool:
    """
    자동으로 화면을 캡쳐한뒤 pdf를 생성한다.

    Args:
        file_name: 생성될 pdf 파일명
                   '실전에서 바로쓰는 Next.js (박수현 역) - 한빛미디어'  # 책이름(저자 or 역자 or 옮김) - 출판사명
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
    Returns:
        bool: 성공여부
    """
    x1 -= margin
    y1 -= margin
    x2 += margin
    y2 += margin

    x = x1  # 캡쳐 시작좌표 x
    y = y1  # 캡쳐 시작좌표 y
    width = x2 - x1  # 캡쳐할 영역의 너비
    height = y2 - y1  # 캡쳐할 영역의 높이
    # capture_region_first_page = ((x + int(diff_width/2)) * res, y * res, (width - diff_width) * res, height * res)
    capture_region_first_page = (x * res, y * res, width * res, height * res)
    capture_region_left_page = (x * res, y * res, (width - diff_width) * res, height * res)
    capture_region_right_page = ((x + diff_width) * res, y * res, (width - diff_width) * res, height * res)
    dir_name = f'./__{file_name}'
    # --------------------------------------------------------------------------------

    print(f'전체화면 {pyautogui.size()}')
    print(f'x = {x}')
    print(f'y = {y}')
    print(f'width = {width}')
    print(f'height = {height}')
    print(f'capture_region_first_page = {capture_region_first_page}')
    print(f'capture_region_left_page = {capture_region_left_page}')
    print(f'capture_region_right_page = {capture_region_right_page}')

    print("\n\n준비하세요.. 5초뒤 시작합니다.\n")
    pyautogui.countdown(5)  # 5초 카운트다운
    # pyautogui.move(100, 0)
    # pyautogui.moveTo(0, 0, duration=1)  # 화면 좌측 상단으로 이동
    # pyautogui.move(-100, 0, duration=1)  # 사실상 좌측 확장 모니터로 이동하게 된다.
    # pyautogui.moveTo(100, 100, duration=1)

    # 생성 디렉터리 체크
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    os.chdir(dir_name)

    # --------------------------------------------------------------------
    # 캡쳐 자동화
    # --------------------------------------------------------------------
    start_time = time.time()

    # 첫 페이지 캡쳐
    capture_region = capture_region_first_page
    print(f'\n캡쳐 1 - {capture_region}')
    _screenshot(capture_region, file_name, 1)
    pyautogui.press("right")
    time.sleep(automation_delay)

    # 페이지 수 까지 반복 캡쳐 수행
    for i in range(2, page_loop + 1):
        capture_region = capture_region_left_page if i % 2 == 1 else capture_region_right_page
        print(f'캡쳐 {i} - {capture_region}')
        _screenshot(capture_region, file_name, i)
        # pyautogui.keyDown("right")
        # pyautogui.keyUp("right")
        pyautogui.press("right")
        pyautogui.sleep(automation_delay)  # 페이지 로딩할 시간을 일정시간(초) 부여 해준다. (가끔 로딩이 완료 되지 않은 상태에서 캡쳐가 되면 글자가 뭉개지기 때문.)

    # --------------------------------------------------------------------
    # 캡쳐 이미지를 pdf 파일로 변환
    # --------------------------------------------------------------------
    print("\n캡쳐완료. pdf 취합중...\n")
    # 이미지 파일 리스트를 가져온다.
    imagepaths = _getFileListAtPath(path='./', ext='png')

    image_list = []
    image_main = None
    for i, image in enumerate(imagepaths):
        if i == 0:
            image_main = Image.open(image).convert('RGB')
        else:
            image_list.append(Image.open(image).convert('RGB'))

    image_main.save(f'{file_name}.pdf', save_all=True, append_images=image_list)

    print('-----------------------------------------------------------')
    print(f'총 소요시간: {time.time() - start_time:.2f}초')
    # --------------------------------------------------------------------

    return True

# end of file