### *경고 : 이 프로그램은 개인의 편의성을 위한 도구이므로 일체의 불법적인 일에 사용해서는 안됩니다.*

<br />

# 개요
**이 프로그램은 파이썬으로 작성된 GUI 프로그램입니다.**  

**이 프로그램은 macOS에서 테스트 되었으며 그외의 OS에서는 정상작동을 보장하지 않습니다.**  

**이 프로그램은 다음 작업을 자동화 해줍니다.**
- 좌에서 우로 한번씩 이동하면서 지정역영을 캡쳐
- 캡쳐완료후 하나의 pdf 파일로 머지
- 이미지파일로 부터 OCR 적용된 개요txt 추출  
  (이 기능은 Naver Clova OCR 서비스의 비밀key, api url를 발급받아 사용해야 합니다.)
- 개요txt 깊이레벨을 자동계산하여 포맷팅
- 완성된 개요txt를 pdf에 적용

<br />

# 설치방법
```bash
$ pip install -r requirements.txt
$ python main.py
```

<br />

# 사용가이드
## 캡쳐자동화 탭
- "캡쳐영역 보이기"를 클릭하여 캡쳐 영역을 지정하기
- 캡쳐 영역은 위치/사이즈 조절이 가능하다.
- 캡쳐 영역이 지정되면 기타 설정값 세팅을 한다.  
  - margin : 사각형의 여백을 추가로 설정하여 실제 캡쳐 영역을 지정합니다.
  - Diff Width : 좌우페이지 인쇄시 여백 차이를 보정하여 캡쳐하기 위한 값입니다.  
    이 값을 잘 보정하면 pdf를 세로로 읽을때 페이지가 좌우로 지그재그 인쇄되어 라인일치가 되지 않는 불편함을 없앨 수 있습니다.
  - Page Loop : 캡쳐 반복 횟수를 지정합니다. (캡쳐 페이지수)
  - Delay : 각 페이지 캡쳐 사이의 지연 시간 (초 단위)
  - 좌측부터 : 표지 캡쳐 이후 2페이지 부터 캡쳐 순서를 좌측부터 시작할지 여부를 설정한다.
- File Name : 생성될 캡쳐파일과 pdf 파일의 이름을 작성

## 개요OCR추출 탭
- 개요가 적힌 이미지 파일을 OCR스캔 적용 할 수 있습니다. 내부적으로 Naver Clova OCR을 사용하고 있습니다.  
  환경설정에서 비밀key와 api_url를 지정하여 사용 해야 합니다.
- OCR스캔 버튼을 클릭하면 수초뒤에 스캔된 개요 텍스트가 개요적용 탭에 전달됩니다.  
  이미지 파일이 많으면 시간이 많이 소요될 수 있습니다.

## 개요적용 탭
- 개요 텍스트를 pdf에 적용 시켜주는 기능을 제공합니다.
- 사전에 준비된 개요 텍스트 파일이 있다면 바로 드래그&드랍하여 사용하거나 사용자가 추가 편집 할 수 있습니다.
- 혹은 개요OCR추출 탭에서 개요이미지 파일을 스캔한뒤 자동으로 넘겨 받을수 있습니다.
- 버튼 기능설명 
  - 편집기 열기 : 환경설정에서 사전에 지정해 놓은 외부 편집기를 열어서 편집합니다. 편집된 내용은 실시간 연동됩니다. 
  - 개요 포맷 : 각 챕터의 깊이를 자동 계산하여 개요 포맷을 자동으로 적용합니다. 
  - 누락페이지 : 페이지가 없는 챕터의 경우 자동으로 페이지를 넣어 줍니다. 직접 편집해도 됩니다.
  - 페이지 + - : 페이지 전체를 증가하거나 감소시킵니다.
  - 개요적용 : 개요텍스트를 pdf에 적용합니다.  

<br />

# 폰트 설정
이 프로그램은 D2Coding 폰트를 사용합니다. 
프로그램과 함께 제공되는 `fonts` 디렉토리의 `D2Coding.ttf` 파일이 자동으로 로드됩니다.
별도의 설정이 필요하지 않습니다.  

<br />

# 개요 작성 샘플
개요 깊이는 공백4칸, 페이지 구분시 `\t (tab)` 사용
```plaintext
저자 소개	4
역자의 말	7
목차	12
CHAPTER 1 웹 프로그래밍의 이해	18
    1.1 웹 프로그래밍이란?	20
    1.2 다양한 웹 클라이언트	21
        1.2.1 웹 브라우저를 사용하여 요청	22
        1.2.2 리눅스 curl 명령을 사용하여 요청	22
        1.2.3 리눅스 telnet을 사용하여 요청	23
        1.2.4 직접 만든 클라이언트로 요청	25
    1.3 프론트엔드와 백엔드	26
        1.3.1 프론트엔드 개발자가 하는 일	27
        1.3.2 백엔드 개발자가 하는 일	28
        1.3.3 HTML, CSS, Javascript 프로그램의 위치	29
    1.4 HTTP 프로토콜	30
        1.4.1 HTTP 메시지의 구조	31
        1.4.2 HTTP 처리 방식	33
        1.4.3 GET과 POST 메소드	34
        1.4.4 상태 코드	35
    1.5 URL 설계	37
        1.5.1 URL을 바라보는 측면	38
        1.5.2 간편 URL	39
        1.5.3 파이썬의 우아한 URL	40
    1.6 웹 애플리케이션 서버	41
        1.6.1 정적 페이지 vs 동적 페이지	42
        1.6.2 CGI 방식의 단점	43
        1.6.3 CGl 방식의 대안 기술	43
        1.6.4 애플리케이션 서버 방식	44
        1.6.5 웹 서버와의 역할 구분	45
CHAPTER 2 파이썬 웹 표준 라이브러리	48
    2.1 웹 라이브러리 구성	50
    2.2 웹 클라이언트 라이브러리	52
        2.2.1 urllib.parse 모듈	53
        2.2.2 urllib.request 모듈	54
        2.2.3 urllib.request 모듈 예제	61
        2.2.4 http.client 모듈	63
        2.2.5 http.client 모듈 예제	68
    2.3 웹 서버 라이브러리	71
        2.3.1 간단한 웹 서버	72
        2.3.2 HTTPServer 및 BaseHTTPRequestHandler 클래스	73
        2.3.3 SimpleHTTPRequestHandler	74
        2.3.4 CGIHTTPRequestHandler 클래스	76
        2.3.5 클래스 간 상속 구조	78
    2.4 CGI / WSGI 라이브러리	79
        2.4.1 CGI 관련 모듈	80
        2.4.2 WSGI 개요	80
        2.4.3 WSGI 서버의 애플리케이션 처리 과정	81
        2.4.4 wsgiref.simple_server 모듈	83
        2.4.5 WSGI 서버 동작 확인	85
APPENDIX	386
    APPENDIX A 외부 라이브러리 requests, beautifulsoup4 맛보기	388
        A.1 외부 라이브러리 설치	389
        A.2 urllib.request 모듈 예제 재작성	389
    APPENDIX B 장고의 데이터베이스 연동	392
        B.1 MysQL/Maria DB 데이터베이스 연동	392
        B.2 PostaresQL 데이터베이스 연동	396
    APPENDIX C HTTP 상태 코드 전체 요약	400
        C.1 상태 코드 레지스트리	400
        C.2 HTTP 상태 코드	400
    APPENDIX D PyCharm 무료 버전 사용하기	406
        D.1 PyCharm Community Edition 설치하기	406
        D.2 PyCharm 초기 설정하기	409
찾아보기	427
```