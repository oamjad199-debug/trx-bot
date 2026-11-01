import os
import re
import json
import time
import hmac
import html
import hashlib
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from functools import wraps
from urllib.parse import parse_qsl

import requests
import telebot
from flask import Flask, request, jsonify, Response, g

# ======================================================================
# الإعدادات
# ======================================================================
TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
import zlib, base64
# الواجهة مضغوطة لتبقى ضمن حد اللصق (100 ألف حرف). لا تعدّلها يدوياً.
_WEBAPP_Z = """
eNrdfety20iy5n8/BSwfG0QbpAjwKtKQj9t2T/u02+4Yyz0XjY4CJEARLZLgASBRapqPsRH7Yx9in2mfZL/MKgCFCyW5Z05074bD
JFGoysrKynsloBeP33x8ffK3n95q82S5OH70gr60hbu6cA7c6EDzgsg5iJLFAd3yXQ9fSz9xtencjWI/cQ4+n3zXHB6kzSt36TsH
14G/WYdRcqBNw1Xir9BtE3jJ3PH862DqN/nC1IJVkATuohlP3YXvWK12CUwy95d+cxouwkiB9KTdxz+echGsLrXIXzgH68hHh5U/
xZzzyJ85B/MkWcejw8MZxsWtizC8WPjuOohb03CZjb2/6+E0ju2XM3cZLG6d124QhaPNxTz59267Pe7j/wD/h+32M9njR3cVhWu/
2Ifue0G8Xri3Trxx1wcC5zi5Xfjx3PcTwicJkoV/fPLnv2pv3Wj14lBcP3oRT6NgnWhxNM0RTfyFfxG5y1YYXRz+EmfXzY0/abrr
deuX+OD4xaEYevzo/PzVm/NPb344Pwc4mvT4kTaKwjDZNpuTi5Ek6LjZvAgX3ujJrDftdW15aeF6NrMm6e3O6Ml0eGRbrryOw1mC
Lp5/5FKXxL+hy/7M8ru4XF4lPiAeuUedIV2D6P4oupi4DbvbM62jgdnvmy3bNnaPtG+2hP5lkDQTd92cBxfzBf4nYv9HSeSu4rUb
gQXGk/CmGQe/BquL0SSMPD9qogUQiHXNSejdbpdudBGsRm008jXtbFNs0UjnXdRNXe6Vbp6483Dpmq8iMKMZY55m7EfBbCxmvnaj
hliYMV67nkfTWr31jSY+2sP1zXgZrJpzn9AdWe329Xw8caeXF1F4tfJGkesRk1/QN7BvWHb7qdbHfzfRevhqWu2nZoUm1sAwlTXT
AMMsgxpieE9AwrRP+UOCardNq9s3bQLVrgElVjW5MBRUm26SuNP5Ep1Gs+DG98bhtR/NFuGmeTOaB57nryRBR6OJPwsjfyulcnRw
MF6HMcQ5XMmhwQrqYdRGc4AuUdO/Rr94tApX/vjXZrDy/BvcDdfuNEhuR62BikewdC/8KuFafSI4f9KK7aeabdeQbmAQUQpL7tk1
1LNaNsOzBbzBEATspvB6PdPuWqY17Jqt/oMBDhngUAAcAmBvWINgr/fbMOxgiwd2HYYPB8g8y5/Efr2nWreO+7q/EUOs+KgO3h5w
Y3eFrWam8SBw2NN+rPlu7IM/muFVAgsxIyPha+4CPLRyEx8M2CI75Efmk42/gIb2zSdkb7YZ/0G5AuZ1zmZWPijvFSfB9PJ2nIRr
sGHas9ceS0U9mi38m7ELFbRqAoFlPJr6xMfjX64wcnbbTDkf64FFm/jJxvdXY6l4mqwbxKcF2uSKw5aKo6AhiFx9s28OwbxdY5zq
QeriQUU1ZwEtfzRZXEUNC+wvhHbfrVQlJkm4HFmYLw4XgacJiScNbOT00Ob2llY6slLU22NSdU1eebpmVp/QuP6IphCXG6HuyP4t
/IQknChBa2x1i8ujKd1I4Zlh2/MvpAZiG2MoFwbpJ+W6YxQJIlXEdBGsR4TpuLYxMyW0FtBoUTUjRASouqvmJFlt2SMZdWh1Uo/z
b0lLwvwq5s2TTfV0rWyqKgPtgVGwKLxYlbRHgD69imL0kEozY8aLKPDG+AVOKzAjrWERXoT78L9nfDpci68vUhBtBQT9lgzGzBbP
XS/cNNpaWyMdV6fYiLdSwdxWOSllMkAAl/AWkIuwVchARFbpxB2MMRE4s7GtAQ2dupFXI/ZyDha1di551f20aX1VHCs7XPA97uDr
PvN1rp3lf9r5ulbbMDSJHTkwZhnek7bXnrQHpvy+u7PV6RUnh+W3Om3eE7OOF+sVf6cLpHKn6h5V1N6visQtctSYZ7Dj1KQRSwm+
aZv0D5ZBMQJREPsajI8wAsAjmaf7rM07W4V5hqkayrVSRbZo6CS4UHirU9Ze8MxTdhkytyDcQQxBuCyS6AFKjJzjwXRmSqeZLKop
HeT/JrW1TyCZ3av7KSQS2j4Ka0Ql9e+kd7dPdNit4Y8aIeoWhShO3Cj57TIk2PiJDQK2hxpY9Al4/6jd07rwpJ7YEzi2R+znfqU4
dGzT6oHfjurEAR6y1qnz1OD5ibkUkSgyNVGl2y0xdR+T0J7gft2mtOXtbrvuLpCpiERZImg77/TB3QnIDsXJ/k0TFhVGGoFaE0I/
Foq+23ua6nkbEcmYNwjwlogMEzha4HBQ0Lhrs45YBJSdrfFMrX4h+FCXFsNjWmv9dHFlny9fpzsDw9+9TLEm60ixXuIi4t+gAHEp
0WLQrrAwXNO7ArZpEE0XfpU57GEprho+zWTt+Jv7/dEobAKjbcHhvNu7rHFHCwqLleU8WEtb3rUVW25Vlj0oeaH+2geeEKj6fVYZ
3Boa4F+ALxCAtAacGGOfND6ZTZAmaJtPJkfDvjUp2AcOF7Wy0Kj20mapoTmGFRvCqh6YFBwJWnHJNe1Q5FOxAFWvLAtLj3rZXi3c
ib+QNog2TvGFy47Lk+kRluhWHOO+cHncZbLdG2ZMIApEv/GFuyajVDJJUkOzgmadLwFi468idfUPW2gJQxUePporBSJzUxli0Suz
HmgxJ347t5j272Yxu3XqtysM5joKL7ZyYYOK6Bwd1URwRe9uaFSsa0VWaRItyHhhsginl+M8j/T0nlnr5VQSMyWwKfN3JW9sn8PQ
N4QlEKqL9QjCeyvWpleTYApN9GvgR42WbbYQrMKmZsRqJjfJ1+gyRZAGRTmycjmaDNzBwFWn0CbbWkdvMw+394XuJFHkhapzExOk
jo5oyIM8cZ25MFVL3S3Eb50cb3/oTSdDFqXrfYFV1QbdF+2VhU+Zu5vPbU2tbrvzECdLMEYufSUGEcq2avaEuk0CJK+3BZTpA4K4
REvCefur5QpR8yzS8L9MfelkpqC2mbPZqcbdwwe5mHsC8YeHaf19YVrVHys7ZLQELV66i0VJmmv5uhDYSmaU+Zqe0MAMb6Lq82Fd
iFMyDunUwYr1MmNA0Ghj7H/NXoGUq6Kg0Uczx0OA2id+QzUX1he2vC4qL+VBqpl4NaMfrGCgg38RRxQ98X0MoejIzHHWWlYvNuVi
GGNuqTBPv8Q7RNKROyUXcZt74Xwo1mgd9bOMXq3eo8FaK5hKLdNTtEyvqmWsBySF7neF01y03avLRZNbXJdwMKr7U2N8K1aqNtEE
/3N8JzmUjJatJMVs6YGJbotJOe9UyWwW3JtOryZbVEaDDsSEP4q04v0RtwxcyNirVqmtykmuEcXxSWlPu1V5qZOOB/mGqfXgdeZR
LnubVVFAduHhdoaDeen0UbAtzQ6faDyZ2WgfimC7yAL9NPdQG3+lYcM+DJH92ierdmwKx5B/yx17ULApzgxEQD2oC6h5OxVRvvQ3
f2007fY/E1ArK9obUM8BT+u27P0BNS1xr6pBgjrN4XHYvPLjGM2dlJ1hR+C5bf/1O57Cj5AJlnw4m/lHk3aBDwXv3z/50cyyO0fm
E9+yPMzAKbnBrD2z/btZywaFj8yBzXx9L2cJNyhYra+Sbb0QD0vnPnVyW7TfVe2C/eMzc157rar5pyyhGkV38wWNZuH0Kt7usztV
R7FTq6T7GcDTCKdN4Wpxe7bNQushhdYeqj2CRSxS+WUXD/fjqyUoerut02/1umxQF+eKCMLfbuaQA452/RGumSBVz3KPT9/1ptNu
ySQMe6mL1FUj8nk3TVZbot2uizLumrhb6+7VxiXFg715FwfwUZw0w1kzuV37W2UMc5GKBrt0IWQteljwZJWCp4KZsn43xz3N6UpO
tmXSO4RbxIebvG6ppbu5N8C/a4Xyj+wg1TJ3WHR5lMSfLXM6YXKTnfRi+0THtryDUGNv2FLmROF/F6MW6lP2bHjfs0Z/gZRNHMRj
VQRX4SZy1yycgRI5qeFLxl58cN6uz8Tc4cVVXZuHH/GUwmRhyYxMZISLV2Yw9yoJ87P0TDja8vSER4MoWOd2T8VMlibutfNyhLLx
U/l9cE/JQGfvMR3d2aX4tMJVkQsIVy9yN2rZhEBVeECMcFPulg+kmp027VC2ACp+kxw5VDPzbSXZcUcMWQgUeWezeqRbQWfFtWt1
7P1JqofkJa0BzkuRNhPVcJmulctj1bW/mkKQiShYIQrLmEflFv9kqr8ocmpZSaHtAfUf++oQcpnJcNYmV4BTcPqUGET1S5DdH1iw
h7kwshoqWm6CS4uqcZkkwoOy11SxH18X61QteI3Gv1/xWrZxT8K3Y4wfnIBMydCSvvi9+zHe74vdq8Dq6i3NukNJI0VLNSWK3PLv
XN9lvVsr97pJQ2qyWwWSlJZdP1Asi3w/VLVO9znXfYVNjuordf573WX2lp8Ipi2rRw4NGQdx/Cjlkvkbsda0wfm055q/um7E7sxv
IpRzm0JziG5wBlIteoTdlxvQV9M3X1eg5vIKMpJx8FN3kn+/JHSqJLGo1sQcQN3276teG+4vGRlWS0bIee6UT9cH4vSccjk1Z+tD
5uLVpCb3It2f35697ChM1+cSiTvV4lfpqXZ9dlixcDKlKHIVqwn+B3v8vXs9WNVuqvAUwWeBUwy26EQW7kHGg7syinmegX9Rvvlv
SIZgszWReLBYuX5NnVnfMLI5vqIMggIUSTAlCqieN8jqNK1Ux3hHBMzyXHTJ//3Sv52hJt+PNUr7bmcR9EQa/LbHtVThqqldEmb9
LKUf8dSuCJgrKLbIsiDHsRX5KJR67Gi7xCU8mqflMZQkojH9tBPlsNQx3coYLs4VK6jFu81I79lo2mmGt/QRK2kNxN1wnuMmkj1X
U99rLkMppXRpbL8xv0m3lH6JdFye4yIqPA6W9HSJi6NdhZGLd3Z8+ObBY7jIz5b6YlM1u67uTxlQPHnp1QVAaW/Q/+6Sg6859UFF
Lh2vqBG2XQxvOvvsmhhOXntN1WXmT9Hi5alLPqC42r2ldKJzEzH1fdolq9MjH10b3gtQLT8dKoI5/Mry0650YVwP4rktVq+lpRfe
dBHGSDNmaai+rbary6zuWtYTVC4l+u4pMqzWWfx/W2pIKWZwiDtZqGTu9VJoWNetzDjDlZBG0vNn7tUiSRPB66sFVGYu9Xz9JxQi
DPamthV1JXqTjmOt9vDjhF2vrnuntkwPNX7QMXjISjxQ9eJQPh1Hj8fgywuutenCjWM8tcWV9njGS9NeiGgqvZOWnx9ogSev8EDS
6uD4//zP//3iUPTlYXObe/AzYfRk19zmZuxTBovquHkOar++0OiZiG/DG+eA87NIwNsHGm2zc0CKUvZEX1A+Ti9wKZjvT5L3eNaL
A+3GApwD7VZ83djOgYUr/srH0sQQBw3JEX4yED3pWvAVntsTeZSDw/0jwCXlMczrd42xSiNEbZk64sVhcVHZ0g/Vtb+QqbspSGb1
8bzhrfgGTKtLc0ThJZ5JvIoWjScXRtog8mjOgYLii7WLmhnQ7Uerr/Xf210on/f4afffD+XP/t/TvUjB1Y+2rPd2Ox1uvbds+duy
MgDp05ASAPjx+oJ545CYg/gSnFjkR5nuEUyXXhzXdBRJDdFP/mbQahdibgyWfJ2xMWtT8PH/+h8ZHwtuzXpkvMx4ytklcOqE0DBH
Sn6t+Y58uuAgkyLSzbQhEETIyN5nDgjcWq6Q4JCEFNdNrcIi5+3pQ5RwL+NE+/zOOT///O783NRO3v75x0+44m9qeP/qw5/OP7z6
8S215hd0C89f/v3jh7eOzo9i0s/zc93UPr4+//TTxxNqlj/RPJZTJRfOBhFguGmdpI97/sWfvFqvx7jVogOV24bBv/0bkNDDxaME
RyVogGB8z0rnNQlFQ5dMoiOc4JvfZgah0mE3dZPpvAFHbCfxePfh3YmDcaRo37iJ++ULPGx5798ckOzYw2kRPTTYuvCTtwuffn57
+85rBPBzZMcPr37+4e3fnC0etPRHOn3qJvzAkY4P3VzPoZJGOn/pJh5gHen4iHUTrh3a6RMXrjfSN4Sdbm5QaINcqS6+cR0kc+JQ
tMhfuomth0ui85e+SxH5+N13b/98/sO7D28+OafpjDQbPmkeuvD0s/GjdPWvP374pDnaFrzJyGt6Vb1Cxu1uQb1m+gL2jUzpa/EQ
c1lppA2koKbuGk9a06YUmn9B+Ji2H2faYdnRjrSj5gCfg2vLcm3NFqWzTfz6vqdeN+1foR1erMPFLcHTOB6F2Bzh6UkMJ6XSk582
qTGhQnQTC6Yd+mOs90fWgNdN2+1qXVEm3Ow2u9/31Wute80LUDT5kVDkA9bjXaZDChGrL0PsNDut4aDQC/N2WlYn62Th/6A16BUJ
JfnxD0Ir28J+/jxQ2YDIM7e610USdLTetdXNegFZzZ5b/etmr0gD2C1b6YXoeN69bnb/XiJCKoS/LxmYyclhsWzhsVhH0mWxhc/S
qxUHIQNwqzWLhKK4NLJYf5RldcVqbOmPpasSKO/r1Red+nf1sYYS0rC4eKGdf9/VU6ikyeHkjokQUeB+Q1uq3TLc6EZ83QqXTOFh
bO5w3mpbxbWRrfnjrGyQL2zA6+rwujpiXYz6nd2JMr+hP309bECn2j+nJRvr35eYqg9vSx/eFj58u8wOtmt1W5B2+kj1Gnnb5UbU
bRXtBrTDXLQpfOT93sof+uwCHniqzmC2eDW2RoYTH50iwsI7+qMYd0wJU55ZGHJirq1+2TCpNghuzc/DeseGoGEHtSERYFjQeBTQ
sarrCNWXarxOfa9Bsdegfro2uWL4N9SOijSmt+j8vyUQvVZH4w/hNCB0bWulxmZ9Y7PaqFHjrzlJHsEJfwQ3SbxdCEk0d/EpCSPk
WylweIcMYkOnW7rx5UujoUQcn1d0SPbsWaWpdYUXtexrbxGsK0A/n4aeD5i6G+lGK17gDUQ4SsKRw6Ng1nj8+d0pdTwzBFrUacxY
xvQUpLOFy7+6WizMxJ2kgQtXf8SimX+/jSJx5Wc/vIAepRvNXKSidlk0ceJcOseNdMpnz9Jfp5dnQPDzu5a/ws8vXy7Hj2ZXK84O
avMGUtImXs0SxWar1boMvNjYCnC+k4VeUwSEiS+jLxqB5WkasugN0fUSuTKtwVC+fNnujBTEtcNtmHXMCQSQ5NJxHJ1ja93Q/Bb/
+kAvZLoea9zHx5qyjgHeuhR9f/Lje+6cXaFzsS/N76MLZiJA3O5TMPoK8wfIEfiNS/OaD341WmNrhgOEhtHCEt7ipTSNqXO8BZyp
4xCBjchPrqIV4LRgwlFm0Zi2VtjmE1S8vZyOSmQ5QU7gA+42PmGq1UVjauB8dccUEnA0Os3OKL6MLxqJsSW0KV6eh5tXCz9KDE29
Qg+5Cje73D1y49vVVMsg4S1SDRIxfiuRQTGkoHq4ThALc4gej7b6X5vvwL9NYmB9RPG2qb8Wp1lNWpDO4TD4lpOheOFTuNJ3O8Ie
GBLkx44DcfeRC0WSGjnXBC+2SOah5+g/ffx0oo+phfo5//Hp44dWzETAETGPFRSnxIFALXLcjRsk2synPAAjj+HGWBJK3IxahERD
TReI+9v4ajpF2bBgfJMkb6RDKhCA7x4pJKYbP4LMLJpyrHbS0Kfn+nNuhLjSMNqnMlGn4fqWdrQRM0UJdYEVUkbBhQuV0qI09yRE
TWlrg2NWX/ZWsBVrDZx5Q+cCVd3cXruLK38Ugy0y7iH6pPwVGOOgJUoSGkoX/8afvg5RpIouOmGmU7/IXyKx1hC0JXY64ZuB79GK
CoQAko1MrCUhgBWST8CJZW+kUyd9l0k/oJZpsghd70dMKBfmyU0k/tMP8XkIvQUGBb94LblFxpY1HFjF8cbiJyjO0jXeEWNv80av
pezJeAepAbtFjZrNuQihfCa8MWI4rhz8H2ucEnzDaUTKW0ngQk86zC6So5UUDfTJdHHl+TEDZagpXKGEBbpq09t0DTmSPGofYQSc
l5dItTn6c5omU4QVUsk5Pflj7HpIxy1u0RFHgV++sGICdVgrFIecno1LOAqSMoPsWA+lyCrMQYcBKcW2/wam4N8wYswX74M4wcTg
O+gDY4z7Mpm7p4PKdepe7IEsefhO4IU+u0folR1ioF+IzcNLlpx8GWMt7cIYKH0UjLhTPltdj0f5UiZXwcL74F43FPUKReAABr6I
6fEFRPmc8vUcnUFqwRSSJRjkCUoFkObbnxI0ZSbxjI1gPigzUMTox1uF14L4lShzcnJR0GAyNRIH7keYSfUCkRd58lzq6UwV2jAF
81LXRNkUzIFumJIso4bhHEuh25npmQegUVo9hyULrXQzM9AjzmyeYtzZzqgZuDPJTqzfw0hBe4n8LfeG7eTeBtNwp1CSXJm/oKAX
C840GGflR7pyWmq3y7XwvYc/cdszdDFjOpdCv4LK5EMBJJDF9A8pzBvmte3yVH74kEcLoJcVqpXIyz4oyEumTbi2hkIvWBMyQMKo
YDC2dI5O/sgHI7E3SjwTwTlusXEaF3zmuOAzm/SJh4EyvSZatwKBca6wJZN8nPyCSVs4NI0b+VmF0Vq668bCOQZasPoBs6MwjHgz
IuOJ9zkuwMQM18xHni7O5NrKO4Nh3K4we9qFtZ10jb/FOcjpqfCwz8xTPhigb5ni559pbv/sLE3nZzzqxM6x9O5iIxX3xuF/nv7n
P9bb9zt8fNidPT+8MiE7LfRbNowCjFcIxepBqBD+EQPGhQCSdfhHjDZT1xTAiq9ytUo+rxs+AohQ0VBJ21mjlBnFMu5q6sN13TTA
Jd5V5Fg4syZyNTIYVGRC/qh05PGO0WTeQg1/wzIbOL9vG4cYh9F4hWqT760BzWpemh0j9cFbdComXUqnkYTf+MA1/I6KFRu28Asu
X1gGrNB/Xflx8io9eP+ODtQbhAD5yw3MVbBPrHu/ZWFR1e+ElK+QIdK/k3rtiw3PdGdDaBbneHKHPlxNoA1zp8IhtwJKEV3uUYhV
bRjsVYQPU4CS1e/FltYYg6MbN87xzWn7DEhnCzBe6kCc0M9xzy3lV6DOb7GrQx08TY4n3dYlzjsRgbvet1fxbep1iV17/f7j6x/O
P/38J+ePnbGo5F8oxSVy93Q03s0TDunK/hgL48TqDWfdaU2oW0jz2f08zYo1yhy2mpzB+Yv180A5g8Kjldc1C50tnVWmw55/uFpO
oPNXuaj3jUzpzZcx6btTVhh4pAKJgviwgwc2DFNtekpNh320xk/77TM2D/kUAA1D/omq8hu2qbfBZS1adAOMnatXfxq/R2GhQ2+2
cY6F9nJvkILhn1M/WDToVrPxhiSDVWFTyjnc6lfJly/5DcM4hH5sG6qOTb1wN3XTMcpx06CAQTg5hGrIAksT4T3Mr7xYVWLhnZEC
HEJDhivhnighTKOEDMGwECaI0ao+IzfTKEQCJKvh9CcR0ChxwfTTnNayFTAeo4uMjShlgYxBONNk7QAlxl57J0sXOQI9BcCzcKT5
E2o6UZ0KDU3uQGPlbzQEJ1QSEHuXuiENCKGQ94RvBp+/DL+xDbyRrGJAeqmFl3evGvEcnozsSZkTJ56niQT82iGUEAE5emXLTOZR
uKGEjPAv8xwNeuRQ43lD6LPSZnKBwCuvgaoqM0gJJNRdumjFASOUBHqnOl0g+yDrM87yXkH8cerkDPnsWfazxdWi8Wlw1kIdBAgc
TjO2oFEvH7IXI9mJ5i9u0jbNHJy73rncD7mEHZ85sBJPIniGGlXNpVV3okmmRpSAJK6wtOsd8jM17KjTO5eDXR7+Po5zzl7KXA3l
bGKOXIFLmgxS5GesKQgqCAheb82WSUqmrRyd8jKyZzJwljfitJkB5KkblSgzPDxcosr+SB+LRd3QGjKFkG6bQEvjiaIWf+9qg/5C
eJ8H9iotvLtowbE9knLwYCUZCnb3PvEn5q9Jfi3IC7+fw7+aO/YQbCGDkyp/7KdUlvI6Dy/PUxC5x6xvo51uzpboHvkb5LaMnIBp
Ikvu5e9BccWwvAZycYNela9YBtfJFABDfOxWNQv9AQNkfUAD13tHIeYJvDy++ilc4zerF1fqj9wNjrGjxSQCJYmd03J0KyrPEXoy
yE/4/XFWILALAgfPLbVpgqZsxoW/ukjmBjuNE/YYGWNoMiT5JHpSZqna+ZyeDDhuG6kwE0X2Rd78tlYuwdZELbXIXNJCsjSDVl2Q
rLrOQvbSY+aq15t5qkriQssWwiR5D2i+B0IXe6zLCYJC9zfl7iUUufAbiSAPefom/4Y8mPCkGqmPo5IrixKYYBl/aFKhCQVLDv/X
U1XUqv/L6bqHrPuI9pqxONHvXqdg4/U0UeLWtvT92DUGzcgjjw9jmez4xhIOXj4aq3buJAhzdZUe5TH0ErlaQqCgHaPpMCBPWYkH
EvTnQP25/hRpJ+MusPRuOgEii8GEuOMe9FNckM5riKJctdqccLMggiqaEoP9CIjnRtJ9ob8fQgcNVX0b84uPfC/fMZZwriXNuBAU
VZhw3+a/Qaj0PQIwXdl8sVnTiVMTDsMCibr8jHtSs5APn2S5Xorhc0s3nUAtjlXEpmmWXhxUFObfOG6LLMNx+2UmlqLFGLWLqG72
ospvuklFXRSdjnQLuG8AlvH/CwAWaByDxhtjJG/SiHxpm0lufgFhTA3qWlOvdVNZ6SZb6aOyikCvLAW7e0TpQDI0yNY1GtKI1Nur
zAI+Fhbwy5fHKOqtehAUfKC0GI+pePn5THbwhURRdPuJU4JhRJkG/TTTi2d6fm6LHGfBoCHNlu+K9J+fI0NFg7EG1p9nihatTWGR
zl2IvNXihYO3N6d4pr7NLnXD5Q06WlP8BMVfJOdJ8ouh4rlxytwjMLmXALyXKgXATykJeLoNzVT1yNhJUxd5F5tJ90g4SEVg0tXZ
A435Uo5WfLkNU1Es1GlLT8jkUBuHLTKS//nd2798crASStI2rhWXaOmkZ4kmq/ol6fnzNF8Lkdmn+5etibugFOhhcYiwAUJeJRcj
dKhkw/gdtZDKDIyS1VQS7fIPTTkNzEd+Dnycz1m2Fmm59Dr8DMmKXoMPhTd4vc8a0wuB9TxFV7lHVkVYg6LNwruZdZGpK7Tzq4vR
X+c///Tqzx8yXV8LnN9ELPQolr23L4hTsEgpEleRnAouKfrI0TCdjcq2ndZa0IdayofbyaV4X0aB0Vdg9CJCtTbxbHR6tmc+vBO2
ZhNwKLgzJUcUk6YZc2QuDTtpzNmcyCc9UrgUkpsm+UHMnBOFkO3lIH596j4WopuSSPRK0ZRKBEhXicD8oj9ftugOEnIq9xtfBRra
8TUb8xx4+paGc35eN4JWMQqnV/T0Z8Ur4zeNyiO6Ox6vyHQjyqFoyB15dPZsysn9y72pffJ0y6n9y2JiX/ZcTPTaFP+lkuDPto+Q
rKoE8fKyUp1GnX/ZK732VO6AeLlZLkilty4VXzXWq3lrS+mVMG2GjO2cuf91Ijdzve9MtPZdaKU3KZVedlZ8vXH2YFU255tUcGh3
wDZ7bESBjlwAAzznHYUXT1Slti4z6XMdVZUpo8rV1J3L1nFwAWrVsUXPN+rcxeKgJdTT7Jz+cqBJPvNHvNBuRBogY08kMrMj27RW
aJdDq/E0i6ydlTblMxmMl6gsyokrUsuNa5Oy0eq5Ij1V94N/66TMjNtKKnPqVMidjsg1Ho15nCZHpvfGAnT3QwjRziEU8uCyYO8B
kCj3E+SH5GnpYLFwpgqowAH4U4Ru150BYJauLA4vwn6soiqzItqzZ9pjpoJMESkZX+Mh61iFHxleYSHblLRp3mmbiwAls2SuiSog
CxVOmaoMMz96n03hATUWL6xVisQZNb4I3gYnQAgrELaYQWr0J72yjRyJ5/rzUObxnusauxVqoHpHdKVyflptSQmR98T2mnKBkxM8
KJvWW8psOt0UN0z9fAKbe0mHzTvegYswM+G77Kjl8bQlnmunUlBDU8kvhEqUGux1bOdu7Dx+vITbeIPcs0dRvepirtViQpyF6NQH
zzaSOzOHRsKj7/oJvCzdTJWJAijXJ5jl2bPHheo4tcaGgon7NAmnjBtZIhFLrwGaejJpBR57Mlkq9IEJdcYdWMhfeK/NWpSqSN96
d0cxXbH0T80YM+HoreuljLDY/tpkMG30zqxdJ4Xroq5G5+g8dq99vWTeq0ZIlp3ssaEQkOpMNNHmE6B7YqLNGz+eEgRQxcQGZco7
9Wd/m3nMqmD2uXj4m1e64hvWREb3GMF0EcV+ewyt8lYtWSY1Qet4g3qu5gRcfTniTzySvSi+8oINtCICX76w6nwlNv8+FJFVn4X3
xwt3WF44KN5emdnP9PkDxttdlt9ZMi9KBn+Z8nG+U6N9pxcZc4uAXK7tW0izYuy58LDALAjn6alz8fAACEcXeHbgDkOfSD3OM5Fz
wvuQWxfUAmxVwzLvijoSRMdVGwF3kXznU+ssq6Oftpg/OOXwigrsHF2cLI7LipYfA1EO34XG2aq5pfSHfJyhJR4Ywcd4fx/6Q9Vc
WMb2FSz0UsefrUbWjliNMERNEpOAAv1CXkS6Slla7MzIy1TrR8iSmrFSfDouFkPlO8GVqJTqpf57ClEzJwdeaiEJ5dNZPPgmKyFF
A5eQIvBfUZKXfJX0IZLW9Fy0wt9F9Sy9zeblXTdHWtFFoskFH1a0j3DBU2z4uO5RMd2/K0TLS19xb+4KQipva6h6guqJMkgp3/5Q
3ZPsRloktvQ5nn9J0cLzQhPVi91VbJ7XaBki6dXK/O38lvRG+L7CPOTBIR1LtKAnOQylil7H+5DmKJ9/lJlZwkD00vZVbuYqQuPX
zcjXUeC1GuJFM4fi77b/X8oZMZk=
"""
WEBAPP_HTML = zlib.decompress(base64.b64decode("".join(_WEBAPP_Z.split()))).decode("utf-8")

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()   # رابط PostgreSQL الخارجي: يحفظ البيانات بعد كل نشر
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "0"))
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

KINDS = ("phone", "app", "site", "ad")

# إعلانات Monetag: مرحلتان (الأولى فيديو 50 مشاهدة، الثانية سريع 100 مشاهدة). كل القيم قابلة للتغيير من متغيرات البيئة
MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
OC_SDK_URL = os.environ.get("OC_SDK_URL", "https://js.onclckvd.com/in-stream-ad-admanager/tma.js")   # Onclicka
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "61543161") if ch.isalnum()) or "61543161"
AD_STAGES = [
    {"fmt": "interstitial", "views": int(os.environ.get("AD_STAGE1_VIEWS", "25")), "reward": float(os.environ.get("AD_REWARD_INTERSTITIAL", "0.0005")), "min": 5},
    {"fmt": "oc", "views": int(os.environ.get("AD_STAGE2_VIEWS", "25")), "reward": float(os.environ.get("AD_REWARD_OC", "0.0005")), "min": 2},
]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "2"))   # الفاصل بين مشاهدة وأخرى
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))        # قفل كل مرحلة بعد جمع رصيدها

def load_offers():
    try:
        raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception:
        raw = []
    if not isinstance(raw, list):
        return {}
    offers = {}
    for o in raw:
        if not isinstance(o, dict):
            continue
        try:
            reward = float(o.get("reward", 0))
        except (ValueError, TypeError):
            continue
        if (o.get("id") and o.get("kind") in KINDS
                and str(o.get("url", "")).startswith("https://") and reward > 0):
            offers[str(o["id"])] = o
    return offers

OFFERS = load_offers()

# ======================================================================
# قاعدة البيانات
# ======================================================================
@contextmanager
def tx_sqlite():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()

_DBPG_Z = """
eNqVWF1v29YZvtevOOAQlGxUwo6xFcggbIrNeEJlOZVlLIWdEjR1bBOmSJqHsuxhN0ntxDWKDbveZTA4yZq2QZdl6S8h/82e9xxS
pL6clBcSefh+Pu/HeQ81Taul79IX2ZP0JXsQiuQg5ltftu+y9FX6ffo+O2cDxwvM6IxlV+nr7HH6P5Z9g9X0OjsH1xX+n6bX6Sum
y5Xn6Zv0bfpj+jL9TpJkF+nPkPRD+mN2kV2CVC2n/0pfy39wmqZpsOxxdsVgw3X6nrjZhGiwX0Pu91h6WYM0GJt9S2ZcpNcsewbO
9AXxKcvA9J/0DUufZ5cMet6DV0p8heVfsqvs3MR99ne48j77W/YP4ngMze8Ynp+SkMv0v+n7wvpXxANxa81e815zy7K3u22zBppr
2PMMgp7BBlCRO9/AEnHsewlfmXEeFkgfczSBAx7Pyf6rsQ5A9DR9lz0pwL0EODUNAfIGURgn7HjIh7x4iMd3yWHMnb4XHNT243DA
3DBI+Gnie3ssJ8hXBk7gHPBYUfW56w0cvyBZU4+1QmYkztwwOrhTq7U3V7+wv7C+Yg32+crSnaU7v1tm7DeIFdnPCN7s4i55obIl
91suq/gS2k9BDKzTn5hE7nUeEZBesjxvfkjfIKg6eP8NMfes9VaHtTY2rLVWs2cp7JCXwNao1exWZ8vq9uzWemeza8GymJtuOIg8
n+ux9vWu+FQR7Irbm138KDq66fQ2d4VWJ4aWUbM3mg/t3p83pyXs7uHFrq7vfK0bjz6tqz9j1ygZu1Zvu9uxW2s3KlfqbusjLzns
x87I8cVfk9gJhOMmXhgIY3dvLLJWc31HCNYNR3oyjHxu3K0xXIh/+jZ7DISRs09QBs8p2wmzN4jBBYvD0c7SI8L1RV5RP+er2p7j
O4HLNbxVqObJaUKHSXlF8vt8n9l2wEe2rbu+qLPAGXD8nTj+kIvcCLpiuCqGEY91w5xgyClLQtOWMkDveyLR5UPlNU+GccDiWkX9
AU9g2AASBff36+yootfbZ57wApGQL/pRnYkkrryuiJSwmbPS6De3yfSCPj/Vj4wZexYxHxmloUf8TMjlKiyKXXpaUUQBJRYZbt9J
uA7w64wL14l4oxcPK/GVnfVStaLz9BeUhsr0DzURtDe8/7ZgKrv3OLgUA+g1AZkXIW6xutF+ryn/ge1kLZkDJ3EP9WrcScYUkRju
6ZpaYpTjDFmMRHDDYZA0lg12m2lss8NWNzv3263VHlvbZJ3N3p9anfXSrKL2pLBYW+9aqPOtnr67TGUmxvYpxCbNEWbMI99BOmi3
QKzduqUZ5dIf5JLIXczjI6bjYff7vi6SQZK7KuXisZQDz6x1q8sedFsbze5XjJpgc7u32eqsdq0Nq9MjPfda64Ch1WxXySZVo76V
j7t7uUhZ9sTakkLGyWIHw4F+khs0mfcn9aJHz+aeFyTgIoYT1miwEzMJbazxg9jxbVmdusG4Lzjb90OHaKvmnYxbz+owFmF8t1KX
XuAl40pAA6umhcx1l/qfMzJdyaobk68hNUEn8vqg6oQBn3yLNzJj8PKz5bLI+Cl3h1QvqnapaiIndgaioRsV/U58QCGTZasrAgmB
ulXuTuok6rnVKEV5ggVhIllKL0ZOkNjS/L0w9PWy7Y/rxGBO0GdaJds1KcdDypnDSLbLaivLJU72L8FuN1AySjqqhHl9bRpoc4xL
XfpuLASzYCiWPqx+OlaFhH0OJwGIbmCLmc46Iqr0cPDmIZvZOYrdYKdPO9V+GLO+xCfX0kcY0JVoR5xRQrthviHt5NUhBZyQAKXo
UaVBjw2ebtJznZpWRrEnkGJKBvkgs0gxkn/xtCrH9xfsBztVLmlyXPV5zG08KssvDIJfU3xYUtX3q2snt1HVu14IM8oUKxnLweQB
KqDcsi4w/mKix6CHQQ5THqb+62Lee6vmWRwC/kmjMTYvvHkrx1tWUCl69fgTTfDPwXSOieaZWqORHzteMdlDBJ0fwPAOfzTET84v
E1j1RQDnvb/wxm+nMcMrYIbfyeVjLMrp2mx7++GXdDfdywQfUAMpZm1ziw+c6DCMgRY0VRKDRqMFSVFM1ZgXg4C7iT5bhtL2/LWd
eAMeDrGlLmEO4TxyfO+Ei8Zy9QnV7PPGylJ9Qlb1PXaCGKUyJcVWu/VKnYWy9ERD+8zFDojmOOBBqXtlCZdW8Q8D0rR7BUCm4x4P
vbiKXRKfTTab0SEGZUYD0OT6XOLiIkCKEj42YYEdhCPHSyqKioufujzKz0qmNYiSBSIrXcyUITM+3hz0CLLIdP1Q8P58mtzsxAuG
fL5PQ+pKSs707jlFNy5MbctqWxiolrXFtNKoRbJIWxz6/p7jHi2gyYEh0kXgWvIPSTPf9YW4jU24ycaP00FXhLZU+zi2cYbG3OfO
jO7Y8QQvUzwaJnkrIWvrbM/pN+7j8MYrOT/jJJICdAyd/sbcuDHHFwLzcaBMACLZYPMsaV5G5CUpLbXtewH2pLMPQqem1YFzxO3k
VEfLynGJsEUgp2mnkKsK0T9OfX8oUAZrtUXK3YwkUH1XICBQG0zCvxh8VUxzJ9FFNRQd2E7/xAPxmX2KA7nth6iJW4KOH3rx1aNu
zAqaF6Mzj/t9uYPrtJNOJdeIPhAMJtrVzQGdmyQkZ0Htfjg9FIrUduck/o3xlyGhXIF+WQp5WItz82meDnILFu4h9kU9OcUGLG/z
CNMXEBlw5gjmlgpoMKJTl5yNJIMpInykkEfUmfqS57P8LDvrYjkizznklXiVZFqz3cP5Dh/22hYbCh4L1lxbwyDf3t7Ax6f7dGhl
1sPWVm+L4UvKAetZD3GYte43t9s99sknmlH7PxOo7Zw=
"""
DB_PG_SRC = zlib.decompress(base64.b64decode("".join(_DBPG_Z.split()))).decode("utf-8")

if DATABASE_URL:
    import types
    db_pg = types.ModuleType("db_pg")
    exec(DB_PG_SRC, db_pg.__dict__)
    tx = db_pg.make_tx(DATABASE_URL)
else:
    tx = tx_sqlite

def init_db():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            balance INTEGER NOT NULL DEFAULT 0,
            referred_by INTEGER,
            trx_address TEXT DEFAULT '',
            first_offer_done INTEGER NOT NULL DEFAULT 0,
            banned INTEGER NOT NULL DEFAULT 0,
            ban_reason TEXT DEFAULT '',
            created_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            offer_id TEXT DEFAULT '',
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            release_at INTEGER NOT NULL,
            approved_at INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at);
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            processed_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS ad_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            fmt TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_progress (
            user_id INTEGER PRIMARY KEY,
            stage INTEGER NOT NULL DEFAULT 0,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            last_view INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_stage (
            user_id INTEGER NOT NULL,
            stage INTEGER NOT NULL,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            opened INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, stage)
        );
        """
    if DATABASE_URL:
        db_pg.init_schema(tx, schema)
        return
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip():
                c.execute(stmt)
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "lang" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT ''")

def ensure_user(conn, uid, username="", referrer=None):
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if row:
        return row
    if referrer:
        ok = referrer != uid and conn.execute("SELECT 1 FROM users WHERE user_id=?", (referrer,)).fetchone()
        referrer = referrer if ok else None
    conn.execute(
        "INSERT INTO users(user_id, username, referred_by, created_at) VALUES(?,?,?,?)",
        (uid, username or "", referrer, int(time.time())),
    )
    return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def active_referrals(conn, uid):
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (uid,)
    ).fetchone()[0]

def ban_user(conn, uid, reason):
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))

def release_matured():
    now = int(time.time())
    unbanned_users = []
    with tx() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE status='pending' AND kind!='referral' AND release_at<=?", (now,)
        ).fetchall()
        for t in rows:
            u = c.execute("SELECT * FROM users WHERE user_id=?", (t["user_id"],)).fetchone()
            if not u or u["banned"]:
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
                continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]:
                c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
            
            ref_id = u["referred_by"]
            if ref_id:
                ref = c.execute("SELECT banned, ban_reason FROM users WHERE user_id=?", (ref_id,)).fetchone()
                commission = int(t["amount"] * REF_PERCENT)
                
                if ref and ref["banned"] and ref["ban_reason"] == 'offer_reversed':
                    refs_count = c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (ref_id,)).fetchone()[0]
                    if refs_count >= 5:
                        c.execute("UPDATE users SET banned=0, ban_reason='' WHERE user_id=?", (ref_id,))
                        unbanned_users.append(ref_id)
                elif ref and not ref["banned"] and commission > 0:
                    cur = c.execute(
                        "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) "
                        "VALUES(?,?,?,?,?,'approved',?,?,?)",
                        ("ref:" + t["txid"], ref_id, "referral", str(u["user_id"]), commission, now, now, now),
                    )
                    if cur.rowcount:
                        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))
    
    for u_id in unbanned_users:
        try:
            bot.send_message(u_id, "🎉 تم فتح حسابك بنجاح لأنك أحضرت 5 إحالات مكتملة! يمكنك الآن استخدام التطبيق.")
        except Exception:
            pass

def _release_loop():
    while True:
        try:
            release_matured()
        except Exception as e:
            print("release error:", e, flush=True)
        time.sleep(300)

# ======================================================================
# التحقق من الهوية
# ======================================================================
def verify_init_data(init_data):
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received = pairs.pop("hash", None)
        if not received:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None

def auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u = verify_init_data(request.headers.get("X-Init-Data", ""))
        if not u or "id" not in u:
            return jsonify(success=False, code="auth"), 401
        g.user = u
        return fn(*a, **k)
    return wrapper

_ip_cache = {}
def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or ""

def is_vpn(ip):
    if not IPQS_KEY or not ip:
        return False
    hit = _ip_cache.get(ip)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    try:
        r = requests.get(
            f"https://www.ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}", params={"strictness": 1}, timeout=5
        ).json()
        bad = bool(r.get("vpn") or r.get("proxy") or r.get("tor") or r.get("active_vpn"))
        _ip_cache[ip] = (time.time(), bad)
        return bad
    except Exception:
        return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username = None
_bot_username_ts = 0.0

def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600:
        return _bot_username
    try:
        got = bot.get_me().username
        _bot_username = got or _bot_username or "TRXEarnBot"
    except Exception:
        _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now
    return _bot_username

# ======================================================================
# API
# ======================================================================
@server.route("/")
def home():
    return "TRX Bot is running 🚀"

@server.route("/api/me")
@auth
def api_me():
    try:
        release_matured()
    except Exception:
        pass
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]:
            return jsonify(success=False, code="banned", reason=u["ban_reason"]), 403
        pending = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)
        ).fetchone()[0]
        refs = active_referrals(c, uid)
    return jsonify(
        success=True, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO,
        pending=pending / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}",
        trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW,
    )

@server.route("/api/offers")
@auth
def api_offers():
    kind = request.args.get("kind", "")
    if kind not in KINDS:
        return jsonify(success=False, code="err"), 400
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    out = [{"id": o["id"], "title": o.get("title", o["id"]), "reward": float(o["reward"]), "url": o["url"].replace("{user_id}", str(uid))} for o in OFFERS.values() if o["kind"] == kind]
    resp = dict(success=True, offers=out)
    if kind == "ad":
        with tx() as c:
            resp["ads"] = ad_state(c, uid, int(time.time()))
    return jsonify(resp)

@server.route("/api/address", methods=["POST"])
@auth
def api_address():
    data = request.get_json(silent=True) or {}
    address = str(data.get("address", "")).strip()
    if not TRX_RE.match(address):
        return jsonify(success=False, code="bad_address")
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        c.execute("UPDATE users SET trx_address=? WHERE user_id=?", (address, uid))
    return jsonify(success=True)

@server.route("/api/withdraw", methods=["POST"])
@auth
def api_withdraw():
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        if not u["trx_address"]: return jsonify(success=False, code="no_address")
        if u["balance"] <= 0 or u["balance"] < MIN_WITHDRAW * MICRO: return jsonify(success=False, code="min_balance")
        if active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        address = u["trx_address"]
        uname = u["username"] or ""
    if ADMIN_ID:
        try:
            fname = str(g.user.get("first_name") or "").strip() or "-"
            bot.send_message(ADMIN_ID,
                "💸 طلب سحب جديد #%d\n\n👤 الاسم: %s\n🔗 اليوزر: %s\n🆔 الآيدي: %d\n💰 المبلغ: %.4f TRX\n📮 عنوان TRX:\n<code>%s</code>\n\n/paid %d  أو  /reject %d"
                % (wid, html.escape(fname), ("@" + html.escape(uname)) if uname else "-", uid, amount / MICRO, html.escape(address), wid, wid),
                parse_mode="HTML")
        except Exception:
            pass
    return jsonify(success=True)

# ======================================================================
# إعلانات Monetag: مراحل مشاهدة، الأرباح تتراكم ثم تُجمع بزر، وبعد آخر مرحلة قفل 24 ساعة
# ======================================================================
def ad_stage_row(conn, uid, i, now):
    """صف تقدم مرحلة واحدة؛ المرحلة الأولى مفتوحة دائماً والتالية تُفتح بعد جمع السابقة، ويُفك القفل بعد 24 ساعة."""
    q = "SELECT * FROM ad_stage WHERE user_id=? AND stage=?"
    r = conn.execute(q, (uid, i)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_stage(user_id,stage,opened) VALUES(?,?,?)", (uid, i, 1 if i == 0 else 0))
        r = conn.execute(q, (uid, i)).fetchone()
    if r["locked_until"] and now >= r["locked_until"]:
        conn.execute("UPDATE ad_stage SET views=0, earned=0, locked_until=0 WHERE user_id=? AND stage=?", (uid, i))
        r = conn.execute(q, (uid, i)).fetchone()
    return r

def ad_last_view(conn, uid):
    r = conn.execute("SELECT last_view FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_progress(user_id) VALUES(?)", (uid,))
        return 0
    return r["last_view"]

def ad_state(conn, uid, now):
    last = ad_last_view(conn, uid)
    wait = max(0, AD_COOLDOWN - (now - last)) if last else 0
    stages = []
    for i, cfg in enumerate(AD_STAGES):
        r = ad_stage_row(conn, uid, i, now)
        lock_left = max(0, r["locked_until"] - now) if r["locked_until"] else 0
        stages.append({
            "idx": i, "id": cfg["fmt"], "target": cfg["views"], "views": r["views"],
            "earned": r["earned"] / MICRO, "open": bool(r["opened"]), "lock_left": lock_left,
            "ready": bool(r["views"] >= cfg["views"] and not lock_left),
        })
    return {"stages": stages, "wait": wait}

def _ad_check(st, wait):
    """يرجع رمز الخطأ إن كانت المرحلة لا تقبل مشاهدة الآن."""
    if st["lock_left"] > 0: return "ad_locked"
    if not st["open"]: return "ad_closed"
    if st["ready"]: return "ad_collect"
    if wait > 0: return "ad_cooldown"
    return None

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    uid = g.user["id"]
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_invalid")
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        fmt = AD_STAGES[i]["fmt"]
        token = secrets.token_urlsafe(24)
        c.execute("INSERT INTO ad_sessions(token,user_id,fmt,created_at) VALUES(?,?,?,?)", (token, uid, fmt, now))
        c.execute("DELETE FROM ad_sessions WHERE created_at<?", (now - 86400,))
    return jsonify(success=True, token=token, fmt=fmt)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    token = str((request.get_json(silent=True) or {}).get("token", ""))
    uid = g.user["id"]
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        s = c.execute("SELECT * FROM ad_sessions WHERE token=? AND user_id=?", (token, uid)).fetchone()
        if not s or s["used"] or now - s["created_at"] > 900:
            return jsonify(success=False, code="ad_invalid")
        idx = [k for k, cfg in enumerate(AD_STAGES) if cfg["fmt"] == s["fmt"]]
        if not idx:
            return jsonify(success=False, code="ad_invalid")
        i = idx[0]; cfg = AD_STAGES[i]
        if now - s["created_at"] < cfg["min"]:
            return jsonify(success=False, code="ad_early")
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        c.execute("UPDATE ad_sessions SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE ad_stage SET views=views+1, earned=earned+? WHERE user_id=? AND stage=?",
                  (int(cfg["reward"] * MICRO), uid, i))
        c.execute("UPDATE ad_progress SET last_view=? WHERE user_id=?", (now, uid))
        out = ad_state(c, uid, now)
    return jsonify(success=True, ads=out)

@server.route("/api/ad/collect", methods=["POST"])
@auth
def api_ad_collect():
    uid = g.user["id"]
    now = int(time.time())
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_notready")
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        r = ad_stage_row(c, uid, i, now)
        st = ad_state(c, uid, now)["stages"][i]
        if st["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if not st["open"] or not st["ready"]:
            return jsonify(success=False, code="ad_notready")
        amount = r["earned"]
        if amount > 0:
            c.execute(
                "INSERT INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
                "VALUES(?,?,?,?,?,'pending',?,?)",
                ("adclaim:%d:%s" % (uid, secrets.token_hex(8)), uid, "ad", "monetag:stage%d" % (i + 1), amount, now, now))
        c.execute("UPDATE ad_stage SET views=0, earned=0, opened=?, locked_until=? WHERE user_id=? AND stage=?",
                  (1 if i == 0 else 0, now + AD_LOCK_HOURS * 3600, uid, i))
        if i + 1 < len(AD_STAGES):
            ad_stage_row(c, uid, i + 1, now)
            c.execute("UPDATE ad_stage SET opened=1 WHERE user_id=? AND stage=?", (uid, i + 1))
        out = ad_state(c, uid, now)
    release_matured()
    return jsonify(success=True, reward=amount / MICRO, ads=out)

def _check_secret():
    if not POSTBACK_SECRET: return Response("postback disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET): return Response("forbidden", 403)
    return None

@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    offer = OFFERS.get(request.args.get("offer_id", ""))
    try:
        uid = int(request.args.get("user_id", ""))
    except ValueError:
        return Response("bad user", 400)
    if not txid or not offer: return Response("bad request", 400)
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    amount = int(float(offer["reward"]) * MICRO)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", (txid, uid, offer["kind"], offer["id"], amount, now, now + hold))
        if not cur.rowcount: return Response("duplicate", 200)
    if hold == 0: release_matured()
    return Response("OK", 200)

@server.route("/postback/reverse")
def postback_reverse():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    uid = None
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed": return Response("OK", 200)
        uid = t["user_id"]
        c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
        lang = user_lang(c, uid)
    try:
        bot.send_message(uid, msg_for(lang, "reversed"))
    except Exception:
        pass
    return Response("OK", 200)

# ======================================================================
# النصوص والترجمات
# ======================================================================
HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Important warning", "💰 Minimum withdrawal", "🚫 Prohibited", "⏳ Earnings verification", "👥 Referrals", "💸 Withdrawals"], "es": ["🌍 Sobre el bot", "⚠️ Aviso importante", "💰 Retiro mínimo", "🚫 Prohibido", "⏳ Verificación", "👥 Referidos", "💸 Retiros"], "de": ["🌍 Über den Bot", "⚠️ Wichtige Warnung", "💰 Mindestauszahlung", "🚫 Verboten", "⏳ Verifizierung", "👥 Empfehlungen", "💸 Auszahlungen"], "fr": ["🌍 À propos", "⚠️ Avertissement important", "💰 Retrait minimum", "🚫 Interdit", "⏳ Vérification", "👥 Parrainage", "💸 Retraits"], "ru": ["🌍 О боте", "⚠️ Важное предупреждение", "💰 Минимум для вывода", "🚫 Запрещено", "⏳ Проверка начислений", "👥 Рефералы", "💸 Вывод"], "pt": ["🌍 Sobre o bot", "⚠️ Aviso importante", "💰 Saque mínimo", "🚫 Proibido", "⏳ Verificação", "👥 Indicações", "💸 Saques"], "nl": ["🌍 Over de bot", "⚠️ Belangrijke waarschuwing", "💰 Minimum opname", "🚫 Verboden", "⏳ Verificatie", "👥 Referrals", "💸 Opnames"], "pl": ["🌍 O bocie", "⚠️ Ważne ostrzeżenie", "💰 Minimalna wypłata", "🚫 Zakazy", "⏳ Weryfikacja", "👥 Polecenia", "💸 Wypłaty"]}

BODIES = {
    "ar": ["البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات", "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.", "السحب متاح مهما كان رصيدك.", "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش", "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.", "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).", "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه."],
    "en": ["A platform to earn from:\n🎬 Watching ads\n📱 Phone-number subscription offers\n📝 Registration offers\n📲 App installs", "Never pay any money to any platform, website or person while using the bot. All tasks are completely free. Anyone asking for money in the bot's name is a scammer, and users who ask others for money will be banned.", "Withdrawal is available at any balance.", "❌ VPN or proxy of any kind\n❌ Wi-Fi (mobile data is required)\n❌ More than one account per person\n❌ Fake data or unreal numbers\n❌ Cheating or manipulating offers", "Rewards for app installs, registrations and phone subscriptions are credited only after verification, which takes 24 to 72 hours (currently {h}h). If you cancel the subscription, uninstall the app or cancel the registration, your account and its earnings are cancelled immediately.", "Earn 3% of your referrals' earnings for life. A referral counts only after the invited user completes at least one successful offer (subscription/registration/install).", "You can withdraw only after bringing a real user who completes their first successful offer, and after reaching the minimum. Every request is reviewed before payment, and accounts that break the rules may be banned and their earnings cancelled."],
    "es": ["Plataforma para ganar con:\n🎬 Ver anuncios\n📱 Suscripciones con número de teléfono\n📝 Registros\n📲 Instalar apps", "No pagues dinero a ninguna plataforma, sitio o persona. Todas las tareas son gratuitas. Quien pida dinero en nombre del bot es un estafador y será bloqueado.", "El retiro está disponible con cualquier saldo.", "❌ VPN o proxy\n❌ Wi-Fi (usa datos móviles)\n❌ Más de una cuenta por persona\n❌ Datos falsos\n❌ Trampas", "El saldo de instalaciones, registros y suscripciones telefónicas se acredita solo tras verificar (24–72 h, ahora {h} h). Si cancelas la suscripción, borras la app o anulas el registro, tu cuenta y ganancias se cancelan de inmediato.", "Ganas 3% de por vida de lo que ganen tus referidos. Un referido cuenta solo cuando completa al menos una oferta exitosa.", "Solo puedes retirar después de traer a un usuario real que complete su primera oferta exitosa y alcanzar el mínimo. Cada solicitud se revisa antes de pagar."],
    "de": ["Plattform zum Verdienen durch:\n🎬 Werbung ansehen\n📱 Telefon-Abos\n📝 Registrierungen\n📲 App-Installationen", "Zahlen Sie niemals Geld an Plattformen, Websites oder Personen. Alle Aufgaben sind kostenlos. Wer im Namen des Bots Geld verlangt, ist ein Betrüger und wird gesperrt.", "Die Auszahlung ist bei jedem Guthaben möglich.", "❌ VPN oder Proxy\n❌ WLAN (Mobilfunkdaten nutzen)\n❌ Mehrere Konten pro Person\n❌ Falsche Daten\n❌ Betrug", "Belohnungen für Installationen, Registrierungen und Telefon-Abos werden erst nach Prüfung gutgeschrieben (24–72 Std., aktuell {h} Std.). Bei Kündigung, Deinstallation oder Abmeldung wird Ihr Konto sofort gelöscht.", "3% lebenslang auf die Einnahmen Ihrer Empfehlungen. Eine Empfehlung zählt erst nach mindestens einem erfolgreichen Angebot.", "Auszahlung nur, nachdem ein echter Nutzer sein erstes erfolgreiches Angebot abgeschlossen hat und das Minimum erreicht ist. Jeder Antrag wird vorher geprüft."],
    "fr": ["Plateforme pour gagner avec :\n🎬 Pubs\n📱 Abonnements par téléphone\n📝 Inscriptions\n📲 Installations d'apps", "Ne payez jamais d'argent à une plateforme, un site ou une personne. Tout est gratuit. Quiconque demande de l'argent au nom du bot est un escroc et sera banni.", "Le retrait est disponible quel que soit le solde.", "❌ VPN ou proxy\n❌ Wi-Fi (utilisez les données mobiles)\n❌ Plusieurs comptes par personne\n❌ Fausses données\n❌ Triche", "Les gains d'installation, d'inscription et d'abonnement téléphonique sont crédités après vérification (24–72 h, actuellement {h} h). Si vous annulez l'abonnement, désinstallez l'app ou annulez l'inscription, votre compte est supprimé immédiatement.", "3% à vie sur les gains de vos filleuls. Un filleul compte seulement après au moins une offre réussie.", "Retrait possible uniquement après qu'un vrai utilisateur parrainé a terminé sa première offre réussie et que le minimum est atteint. Chaque demande est examinée avant paiement."],
    "ru": ["Платформа для заработка на:\n🎬 Просмотре рекламы\n📱 Подписках по номеру телефона\n📝 Регистрациях\n📲 Установке приложений", "Никому не платите деньги. Все задания бесплатны. Тот, кто просит деньги от имени бота, — мошенник и будет заблокирован.", "Вывод доступен при любом балансе.", "❌ VPN или прокси\n❌ Wi-Fi (используйте мобильный интернет)\n❌ Несколько аккаунтов\n❌ Фейковые данные\n❌ Обман", "Начисления за установки, регистрации и подписки по телефону зачисляются только после проверки (24–72 ч, сейчас {h} ч). Если вы отмените подписку, удалите приложение или отмените регистрацию, аккаунт будет аннулирован сразу.", "3% пожизненно от заработка рефералов. Реферал засчитывается после хотя бы одного успешного задания.", "Вывод возможен только после того, как реальный приглашённый пользователь выполнит первое успешное задание, и при достижении минимума. Каждая заявка проверяется."],
    "pt": ["Plataforma para ganhar com:\n🎬 Anúncios\n📱 Assinaturas por telefone\n📝 Registros\n📲 Instalação de apps", "Não pague dinheiro a nenhuma plataforma, site ou pessoa. Tudo é gratuito. Quem pedir dinheiro em nome do bot é golpista e será banido.", "O saque está disponível com qualquer saldo.", "❌ VPN ou proxy\n❌ Wi-Fi (use dados móveis)\n❌ Contas múltiplas\n❌ Dados falsos\n❌ Trapaças", "Os ganhos de instalações, registros e assinaturas por telefone só são creditados após verificação (24–72 h, atualmente {h} h). Se cancelar a assinatura, desinstalar o app ou cancelar o registro, sua conta será cancelada imediatamente.", "3% vitalício sobre os ganhos dos seus indicados. A indicação só conta após ao menos uma oferta bem-sucedida.", "O saque só é possível depois que um usuário real indicado concluir a primeira oferta bem-sucedida e o mínimo for atingido. Cada pedido é revisado antes do pagamento."],
    "nl": ["Platform om te verdienen met:\n🎬 Advertenties\n📱 Telefoonabonnementen\n📝 Registraties\n📲 App-installaties", "Betaal nooit geld aan een platform, website of persoon. Alles is gratis. Wie namens de bot geld vraagt is een oplichter en wordt geblokkeerd.", "Opnemen is mogelijk bij elk saldo.", "❌ VPN of proxy\n❌ Wi-Fi (gebruik mobiele data)\n❌ Meerdere accounts\n❌ Nepgegevens\n❌ Valsspelen", "Beloningen voor installaties, registraties en telefoonabonnementen worden pas na verificatie bijgeschreven (24–72 uur, nu {h} uur). Bij opzeggen, verwijderen van de app of annuleren van de registratie wordt je account direct geannuleerd.", "3% levenslang van de winst van je referrals. Een referral telt pas na minstens één geslaagde aanbieding.", "Opnemen kan pas nadat een echte genodigde zijn eerste geslaagde aanbieding heeft voltooid en het minimum is bereikt. Elk verzoek wordt eerst beoordeeld."],
    "pl": ["Platforma do zarabiania na:\n🎬 Reklamach\n📱 Subskrypcjach telefonicznych\n📝 Rejestracjach\n📲 Instalacji aplikacji", "Nigdy nie płać żadnej platformie, stronie ani osobie. Wszystko jest darmowe. Kto żąda pieniędzy w imieniu bota, jest oszustem i zostanie zablokowany.", "Wypłata jest dostępna przy każdym saldzie.", "❌ VPN lub proxy\n❌ Wi-Fi (używaj danych mobilnych)\n❌ Wiele kont\n❌ Fałszywe dane\n❌ Oszustwa", "Nagrody za instalacje, rejestracje i subskrypcje telefoniczne są dodawane dopiero po weryfikacji (24–72 godz., obecnie {h} godz.). Anulowanie subskrypcji, usunięcie aplikacji lub rejestracji natychmiast anuluje konto.", "3% dożywotnio od zarobków poleconych. Polecenie liczy się po co najmniej jednej udanej ofercie.", "Wypłata możliwa dopiero po tym, jak prawdziwy zaproszony użytkownik ukończy pierwszą udaną ofertę i osiągniesz minimum. Każdy wniosek jest sprawdzany."]
}

TERMS_TITLE = {"ar": "📜 شروط وأحكام TRX Earn Bot", "en": "📜 TRX Earn Bot Terms & Conditions", "es": "📜 Términos de TRX Earn Bot", "de": "📜 AGB von TRX Earn Bot", "fr": "📜 Conditions de TRX Earn Bot", "ru": "📜 Условия TRX Earn Bot", "pt": "📜 Termos do TRX Earn Bot", "nl": "📜 Voorwaarden van TRX Earn Bot", "pl": "📜 Regulamin TRX Earn Bot"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق المصغر 🚀", "en": "I Agree & Open Mini App 🚀", "es": "Aceptar y abrir Mini App 🚀", "de": "Zustimmen & Mini App öffnen 🚀", "fr": "Accepter et ouvrir l'App 🚀", "ru": "Согласен, открыть Mini App 🚀", "pt": "Concordar e abrir Mini App 🚀", "nl": "Akkoord & Mini App openen 🚀", "pl": "Zgadzam się i otwórz 🚀"}
LANGS = list(HEADS.keys())

def terms_sections(lang):
    lang = lang if lang in HEADS else "en"
    bodies = [b.replace("{min}", str(MIN_WITHDRAW)).replace("{h}", str(VERIFY_HOURS)) for b in BODIES[lang]]
    return [[h, b] for h, b in zip(HEADS[lang], bodies)]

def terms_html(lang):
    lang = lang if lang in HEADS else "en"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in terms_sections(lang):
        parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b)}\n")
    return "\n".join(parts)

UI = {
    "en": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Phone Subscription", "apps": "📲 Install Apps", "sites": "🌐 Register on Sites", "wallet": "💳 Wallet", "withdraw": "💸 Withdraw", "watch": "▶️ Watch & Earn", "terms": "📜 Terms", "menu": "Menu ⚙️", "welcome": "Welcome", "bal": "Current TRX balance", "pend": "Pending verification", "minline": "Minimum withdrawal: {n} TRX", "faqT": "❓ Important Rules & Instructions", "faqD": "💸 **Withdrawal:** You can withdraw after reaching the minimum and bringing 1 real completed referral.\n👥 **Referrals:** Earn 3% for life from your referrals' earnings.\n🚫 **Cancelling Offers:** If you cancel a subscription or delete an app, your account will be suspended. To unlock it, you must bring 5 completed referrals OR complete a new successful offer.", "refT": "👥 Referral system (3%)", "refCnt": "Active referrals", "refD": "Share your link and earn 3% of your referrals' earnings for life. A referral counts only after they complete one successful offer.", "copy": "Copy referral link 🔗", "copied": "Copied! 📋", "noOffers": "No offers available right now.", "go": "Start ✅", "reward": "Reward", "pendNote": "Credited after verification (24–72h). Cancelling = account ban.", "wDesc": "Enter your TRX (TRC20) wallet address:", "save": "Save 💾", "change": "Change 🔄", "wSaved": "Saved address:", "noAddr": "No address added yet", "wdBtn": "Request withdrawal 🚀", "wdInfo": "Your whole balance is withdrawn. Needs min {n} TRX and one real active referral.", "lang": "🌐 Language", "loading": "Loading…", "c_auth": "Session expired. Please close and reopen the app from the bot.", "c_banned": "Your account has been banned for breaking the terms.", "c_vpn": "VPN/Proxy detected. Turn it off and use mobile data.", "c_bad_address": "Invalid TRX address.", "c_ok_addr": "Address saved 💾", "c_no_address": "Please add your TRX wallet address first.", "c_min_balance": "Your balance is below the minimum withdrawal.", "c_need_referral": "You need one real referral who completed their first successful offer.", "c_pending_exists": "You already have a pending withdrawal.", "c_ok_withdraw": "Withdrawal request submitted 🚀", "c_err": "Something went wrong. Try again."},
    "ar": {"home": "🏠 الرئيسية", "ref": "👥 الإحالة", "phone": "📱 الربح من الاشتراك برقم هاتف", "apps": "📲 الربح من تثبيت تطبيقات", "sites": "🌐 الربح من التسجيل في المواقع", "wallet": "💳 المحفظة", "withdraw": "💸 السحب", "watch": "▶️ الربح من المشاهدة", "terms": "📜 الشروط والأحكام", "menu": "القائمة ⚙️", "welcome": "مرحباً بك", "bal": "رصيد TRX الحالي", "pend": "قيد التحقق", "minline": "الحد الأدنى للسحب: {n} TRX", "faqT": "❓ قواعد وتعليمات هامة", "faqD": "💸 **السحب:** يمكنك السحب بعد وصولك للحد الأدنى وإحضار إحالة حقيقية واحدة مكتملة.\n👥 **الإحالات:** تحصل على 3% مدى الحياة من أرباح إحالاتك.\n🚫 **إلغاء العروض:** في حال قمت بإلغاء اشتراك أو حذف تطبيق، سيتم إيقاف حسابك. لفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً) أو إكمال عرض ناجح جديد.", "refT": "👥 نظام الإحالة (3%)", "refCnt": "عدد إحالاتك النشطة", "refD": "شارك رابطك وخذ 3% من أرباح من تدعوه مدى الحياة. لا تُحتسب الإحالة إلا بعد إكمال المدعو عرضاً ناجحاً.", "copy": "نسخ رابط الإحالة 🔗", "copied": "تم النسخ! 📋", "noOffers": "لا توجد عروض متاحة حالياً.", "go": "ابدأ ✅", "reward": "المكافأة", "pendNote": "تُضاف بعد التحقق (24–72 ساعة). الإلغاء = حظر الحساب.", "wDesc": "أدخل عنوان محفظة TRX (TRC20) الخاصة بك:", "save": "حفظ 💾", "change": "تغيير 🔄", "wSaved": "العنوان المحفوظ:", "noAddr": "لم تضف عنواناً بعد", "wdBtn": "طلب السحب 🚀", "wdInfo": "يتم سحب كامل رصيدك. الشرط: {n} TRX كحد أدنى + إحالة حقيقية نشطة.", "lang": "🌐 اللغة", "loading": "جارٍ التحميل…", "c_auth": "انتهت الجلسة. أغلق التطبيق وافتحه من البوت من جديد.", "c_banned": "تم حظر حسابك لمخالفة الشروط.", "c_vpn": "تم اكتشاف VPN/بروكسي. أطفئه واستخدم بيانات الجوال.", "c_bad_address": "عنوان TRX غير صحيح.", "c_ok_addr": "تم حفظ العنوان 💾", "c_no_address": "أضف عنوان محفظة TRX أولاً.", "c_min_balance": "رصيدك أقل من الحد الأدنى للسحب.", "c_need_referral": "يجب أن تُحضر مستخدماً حقيقياً أكمل أول عرض ناجح له.", "c_pending_exists": "لديك طلب سحب قيد المراجعة.", "c_ok_withdraw": "تم تقديم طلب السحب 🚀", "c_err": "حدث خطأ. حاول مرة أخرى."},
    "es": {"home": "🏠 Inicio", "ref": "👥 Referidos", "phone": "📱 Suscripción telefónica", "apps": "📲 Instalar apps", "sites": "🌐 Registrarse en sitios", "wallet": "💳 Billetera", "withdraw": "💸 Retirar", "watch": "▶️ Ver y ganar", "terms": "📜 Términos", "menu": "Menú ⚙️", "welcome": "Bienvenido", "bal": "Saldo actual de TRX", "pend": "Pendiente de verificación", "minline": "Retiro mínimo: {n} TRX", "faqT": "❓ Reglas e instrucciones importantes", "faqD": "💸 **Retiro:** Puedes retirar al alcanzar el mínimo y traer 1 referido real completado.\n👥 **Referidos:** Gana 3% de por vida de las ganancias de tus referidos.\n🚫 **Cancelar ofertas:** Si cancelas una suscripción o eliminas una app, tu cuenta será suspendida. Para desbloquearla, debes traer 5 referidos completados O completar una nueva oferta exitosa.", "refT": "👥 Sistema de referidos (3%)", "refCnt": "Referidos activos", "refD": "Comparte tu enlace y gana el 3% de las ganancias de tus referidos de por vida. Un referido cuenta solo cuando completa una oferta exitosa.", "copy": "Copiar enlace de referido 🔗", "copied": "¡Copiado! 📋", "noOffers": "No hay ofertas disponibles ahora.", "go": "Empezar ✅", "reward": "Recompensa", "pendNote": "Se acredita tras la verificación (24–72 h). Cancelar = bloqueo de la cuenta.", "wDesc": "Introduce tu dirección de billetera TRX (TRC20):", "save": "Guardar 💾", "change": "Cambiar 🔄", "wSaved": "Dirección guardada:", "noAddr": "Aún no has añadido una dirección", "wdBtn": "Solicitar retiro 🚀", "wdInfo": "Se retira todo tu saldo. Requiere un mínimo de {n} TRX y un referido real activo.", "lang": "🌐 Idioma", "loading": "Cargando…", "c_auth": "La sesión expiró. Cierra y vuelve a abrir la app desde el bot.", "c_banned": "Tu cuenta fue bloqueada por incumplir los términos.", "c_vpn": "Se detectó VPN/proxy. Desactívalo y usa datos móviles.", "c_bad_address": "Dirección TRX no válida.", "c_ok_addr": "Dirección guardada 💾", "c_no_address": "Primero añade tu dirección de billetera TRX.", "c_min_balance": "Tu saldo es inferior al retiro mínimo.", "c_need_referral": "Necesitas un referido real que haya completado su primera oferta exitosa.", "c_pending_exists": "Ya tienes un retiro pendiente.", "c_ok_withdraw": "Solicitud de retiro enviada 🚀", "c_err": "Algo salió mal. Inténtalo de nuevo."},
    "de": {"home": "🏠 Startseite", "ref": "👥 Empfehlungen", "phone": "📱 Telefon-Abo", "apps": "📲 Apps installieren", "sites": "🌐 Auf Websites registrieren", "wallet": "💳 Wallet", "withdraw": "💸 Auszahlen", "watch": "▶️ Ansehen & verdienen", "terms": "📜 AGB", "menu": "Menü ⚙️", "welcome": "Willkommen", "bal": "Aktuelles TRX-Guthaben", "pend": "Wird geprüft", "minline": "Mindestauszahlung: {n} TRX", "faqT": "❓ Wichtige Regeln & Anweisungen", "faqD": "💸 **Auszahlung:** Du kannst auszahlen, wenn du das Minimum erreichst und 1 echte abgeschlossene Empfehlung bringst.\n👥 **Empfehlungen:** Verdiene lebenslang 3% an den Einnahmen deiner Empfehlungen.\n🚫 **Angebote abbrechen:** Wenn du ein Abo kündigst oder eine App löschst, wird dein Konto gesperrt. Um es zu entsperren, musst du 5 abgeschlossene Empfehlungen bringen ODER ein neues erfolgreiches Angebot abschließen.", "refT": "👥 Empfehlungssystem (3%)", "refCnt": "Aktive Empfehlungen", "refD": "Teile deinen Link und erhalte lebenslang 3% der Einnahmen deiner Empfehlungen. Eine Empfehlung zählt erst nach einem erfolgreichen Angebot.", "copy": "Empfehlungslink kopieren 🔗", "copied": "Kopiert! 📋", "noOffers": "Derzeit keine Angebote verfügbar.", "go": "Start ✅", "reward": "Belohnung", "pendNote": "Gutschrift nach Prüfung (24–72 Std.). Abbruch = Kontosperre.", "wDesc": "Gib deine TRX-Wallet-Adresse (TRC20) ein:", "save": "Speichern 💾", "change": "Ändern 🔄", "wSaved": "Gespeicherte Adresse:", "noAddr": "Noch keine Adresse hinzugefügt", "wdBtn": "Auszahlung anfordern 🚀", "wdInfo": "Dein gesamtes Guthaben wird ausgezahlt. Erfordert mindestens {n} TRX und eine echte aktive Empfehlung.", "lang": "🌐 Sprache", "loading": "Wird geladen…", "c_auth": "Sitzung abgelaufen. Schließe die App und öffne sie erneut über den Bot.", "c_banned": "Dein Konto wurde wegen Verstoßes gegen die Bedingungen gesperrt.", "c_vpn": "VPN/Proxy erkannt. Schalte es aus und nutze mobile Daten.", "c_bad_address": "Ungültige TRX-Adresse.", "c_ok_addr": "Adresse gespeichert 💾", "c_no_address": "Füge zuerst deine TRX-Wallet-Adresse hinzu.", "c_min_balance": "Dein Guthaben liegt unter der Mindestauszahlung.", "c_need_referral": "Du brauchst eine echte Empfehlung, die ihr erstes erfolgreiches Angebot abgeschlossen hat.", "c_pending_exists": "Du hast bereits eine offene Auszahlung.", "c_ok_withdraw": "Auszahlungsantrag gesendet 🚀", "c_err": "Etwas ist schiefgelaufen. Versuche es erneut."},
    "fr": {"home": "🏠 Accueil", "ref": "👥 Parrainage", "phone": "📱 Abonnement téléphone", "apps": "📲 Installer des apps", "sites": "🌐 S'inscrire sur des sites", "wallet": "💳 Portefeuille", "withdraw": "💸 Retirer", "watch": "▶️ Regarder et gagner", "terms": "📜 Conditions", "menu": "Menu ⚙️", "welcome": "Bienvenue", "bal": "Solde TRX actuel", "pend": "En cours de vérification", "minline": "Retrait minimum : {n} TRX", "faqT": "❓ Règles et instructions importantes", "faqD": "💸 **Retrait:** Vous pouvez retirer après avoir atteint le minimum et apporté 1 vrai filleul complété.\n👥 **Parrainage:** Gagnez 3% à vie sur les gains de vos filleuls.\n🚫 **Annuler des offres:** Si vous annulez un abonnement ou supprimez une app, votre compte sera suspendu. Pour le débloquer, vous devez apporter 5 filleuls complétés OU compléter une nouvelle offre réussie.", "refT": "👥 Système de parrainage (3%)", "refCnt": "Filleuls actifs", "refD": "Partagez votre lien et gagnez 3% des gains de vos filleuls à vie. Un filleul compte seulement après une offre réussie.", "copy": "Copier le lien de parrainage 🔗", "copied": "Copié ! 📋", "noOffers": "Aucune offre disponible pour le moment.", "go": "Commencer ✅", "reward": "Récompense", "pendNote": "Crédité après vérification (24–72 h). Annuler = compte banni.", "wDesc": "Entrez votre adresse de portefeuille TRX (TRC20) :", "save": "Enregistrer 💾", "change": "Modifier 🔄", "wSaved": "Adresse enregistrée :", "noAddr": "Aucune adresse ajoutée", "wdBtn": "Demander le retrait 🚀", "wdInfo": "Tout votre solde est retiré. Il faut au minimum {n} TRX et un vrai filleul actif.", "lang": "🌐 Langue", "loading": "Chargement…", "c_auth": "Session expirée. Fermez l'app et rouvrez-la depuis le bot.", "c_banned": "Votre compte a été banni pour non-respect des conditions.", "c_vpn": "VPN/proxy détecté. Désactivez-le et utilisez les données mobiles.", "c_bad_address": "Adresse TRX invalide.", "c_ok_addr": "Adresse enregistrée 💾", "c_no_address": "Ajoutez d'abord votre adresse de portefeuille TRX.", "c_min_balance": "Votre solde est inférieur au retrait minimum.", "c_need_referral": "Il vous faut un vrai filleul ayant terminé sa première offre réussie.", "c_pending_exists": "Vous avez déjà un retrait en attente.", "c_ok_withdraw": "Demande de retrait envoyée 🚀", "c_err": "Une erreur s'est produite. Réessayez."},
    "ru": {"home": "🏠 Главная", "ref": "👥 Рефералы", "phone": "📱 Подписка по телефону", "apps": "📲 Установка приложений", "sites": "🌐 Регистрация на сайтах", "wallet": "💳 Кошелёк", "withdraw": "💸 Вывод", "watch": "▶️ Смотреть и зарабатывать", "terms": "📜 Условия", "menu": "Меню ⚙️", "welcome": "Добро пожаловать", "bal": "Текущий баланс TRX", "pend": "На проверке", "minline": "Минимальный вывод: {n} TRX", "faqT": "❓ Важные правила и инструкции", "faqD": "💸 **Вывод:** Вы можете вывести средства после достижения минимума и привлечения 1 реального завершенного реферала.\n👥 **Рефералы:** Получайте 3% пожизненно от заработка ваших рефералов.\n🚫 **Отмена предложений:** Если вы отмените подписку или удалите приложение, ваш аккаунт будет заблокирован. Чтобы разблокировать его, вы должны привлечь 5 завершенных рефералов ИЛИ выполнить новое успешное предложение.", "refT": "👥 Реферальная система (3%)", "refCnt": "Активные рефералы", "refD": "Поделитесь ссылкой и получайте 3% от заработка рефералов пожизненно. Реферал засчитывается только после одного успешного задания.", "copy": "Копировать реферальную ссылку 🔗", "copied": "Скопировано! 📋", "noOffers": "Сейчас нет доступных предложений.", "go": "Начать ✅", "reward": "Награда", "pendNote": "Начисляется после проверки (24–72 ч). Отмена = блокировка аккаунта.", "wDesc": "Введите адрес вашего кошелька TRX (TRC20):", "save": "Сохранить 💾", "change": "Изменить 🔄", "wSaved": "Сохранённый адрес:", "noAddr": "Адрес ещё не добавлен", "wdBtn": "Запросить вывод 🚀", "wdInfo": "Выводится весь баланс. Нужно минимум {n} TRX и один реальный активный реферал.", "lang": "🌐 Язык", "loading": "Загрузка…", "c_auth": "Сессия истекла. Закройте приложение и откройте его снова через бота.", "c_banned": "Ваш аккаунт заблокирован за нарушение условий.", "c_vpn": "Обнаружен VPN/прокси. Отключите его и используйте мобильный интернет.", "c_bad_address": "Неверный адрес TRX.", "c_ok_addr": "Адрес сохранён 💾", "c_no_address": "Сначала добавьте адрес кошелька TRX.", "c_min_balance": "Ваш баланс ниже минимального для вывода.", "c_need_referral": "Нужен один реальный реферал, выполнивший первое успешное задание.", "c_pending_exists": "У вас уже есть заявка на вывод в обработке.", "c_ok_withdraw": "Заявка на вывод отправлена 🚀", "c_err": "Что-то пошло не так. Попробуйте ещё раз."},
    "pt": {"home": "🏠 Início", "ref": "👥 Indicações", "phone": "📱 Assinatura por telefone", "apps": "📲 Instalar apps", "sites": "🌐 Registrar em sites", "wallet": "💳 Carteira", "withdraw": "💸 Sacar", "watch": "▶️ Assistir e ganhar", "terms": "📜 Termos", "menu": "Menu ⚙️", "welcome": "Bem-vindo", "bal": "Saldo atual de TRX", "pend": "Aguardando verificação", "minline": "Saque mínimo: {n} TRX", "faqT": "❓ Regras e instruções importantes", "faqD": "💸 **Saque:** Você pode sacar após atingir o mínimo e trazer 1 indicado real concluído.\n👥 **Indicações:** Ganhe 3% para sempre dos ganhos dos seus indicados.\n🚫 **Cancelar ofertas:** Se você cancelar uma assinatura ou excluir um app, sua conta será suspensa. Para desbloquear, você deve trazer 5 indicados concluídos OU concluir uma nova oferta bem-sucedida.", "refT": "👥 Sistema de indicações (3%)", "refCnt": "Indicações ativas", "refD": "Compartilhe seu link e ganhe 3% dos ganhos dos seus indicados para sempre. Uma indicação só conta depois de uma oferta bem-sucedida.", "copy": "Copiar link de indicação 🔗", "copied": "Copiado! 📋", "noOffers": "Nenhuma oferta disponível no momento.", "go": "Começar ✅", "reward": "Recompensa", "pendNote": "Creditado após a verificação (24–72 h). Cancelar = conta banida.", "wDesc": "Digite o endereço da sua carteira TRX (TRC20):", "save": "Salvar 💾", "change": "Alterar 🔄", "wSaved": "Endereço salvo:", "noAddr": "Nenhum endereço adicionado ainda", "wdBtn": "Solicitar saque 🚀", "wdInfo": "Todo o seu saldo é sacado. Exige no mínimo {n} TRX e um indicado real ativo.", "lang": "🌐 Idioma", "loading": "Carregando…", "c_auth": "Sessão expirada. Feche o app e abra-o novamente pelo bot.", "c_banned": "Sua conta foi banida por violar os termos.", "c_vpn": "VPN/proxy detectado. Desative e use dados móveis.", "c_bad_address": "Endereço TRX inválido.", "c_ok_addr": "Endereço salvo 💾", "c_no_address": "Adicione primeiro o endereço da sua carteira TRX.", "c_min_balance": "Seu saldo está abaixo do saque mínimo.", "c_need_referral": "Você precisa de um indicado real que tenha concluído a primeira oferta bem-sucedida.", "c_pending_exists": "Você já tem um saque pendente.", "c_ok_withdraw": "Pedido de saque enviado 🚀", "c_err": "Algo deu errado. Tente novamente."},
    "nl": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Telefoonabonnement", "apps": "📲 Apps installeren", "sites": "🌐 Registreren op sites", "wallet": "💳 Wallet", "withdraw": "💸 Opnemen", "watch": "▶️ Kijken en verdienen", "terms": "📜 Voorwaarden", "menu": "Menu ⚙️", "welcome": "Welkom", "bal": "Huidig TRX-saldo", "pend": "In afwachting van verificatie", "minline": "Minimum opname: {n} TRX", "faqT": "❓ Belangrijke regels & instructies", "faqD": "💸 **Opname:** Je kunt opnemen na het bereiken van het minimum en het aanbrengen van 1 echte voltooide referral.\n👥 **Referrals:** Verdien levenslang 3% van de winst van je referrals.\n🚫 **Aanbiedingen annuleren:** Als je een abonnement opzegt of een app verwijdert, wordt je account geblokkeerd. Om het te deblokkeren, moet je 5 voltooide referrals aanbrengen OF een nieuwe succesvolle aanbieding voltooien.", "refT": "👥 Referralsysteem (3%)", "refCnt": "Actieve referrals", "refD": "Deel je link en verdien levenslang 3% van de winst van je referrals. Een referral telt pas na één geslaagde aanbieding.", "copy": "Referrallink kopiëren 🔗", "copied": "Gekopieerd! 📋", "noOffers": "Er zijn nu geen aanbiedingen beschikbaar.", "go": "Start ✅", "reward": "Beloning", "pendNote": "Bijgeschreven na verificatie (24–72 uur). Annuleren = account geblokkeerd.", "wDesc": "Voer je TRX-walletadres (TRC20) in:", "save": "Opslaan 💾", "change": "Wijzigen 🔄", "wSaved": "Opgeslagen adres:", "noAddr": "Nog geen adres toegevoegd", "wdBtn": "Opname aanvragen 🚀", "wdInfo": "Je hele saldo wordt opgenomen. Vereist minimaal {n} TRX en één echte actieve referral.", "lang": "🌐 Taal", "loading": "Laden…", "c_auth": "Sessie verlopen. Sluit de app en open hem opnieuw via de bot.", "c_banned": "Je account is geblokkeerd wegens schending van de voorwaarden.", "c_vpn": "VPN/proxy gedetecteerd. Schakel het uit en gebruik mobiele data.", "c_bad_address": "Ongeldig TRX-adres.", "c_ok_addr": "Adres opgeslagen 💾", "c_no_address": "Voeg eerst je TRX-walletadres toe.", "c_min_balance": "Je saldo is lager dan de minimale opname.", "c_need_referral": "Je hebt één echte referral nodig die zijn eerste geslaagde aanbieding heeft voltooid.", "c_pending_exists": "Je hebt al een openstaande opname.", "c_ok_withdraw": "Opnameverzoek verzonden 🚀", "c_err": "Er ging iets mis. Probeer het opnieuw."},
    "pl": {"home": "🏠 Start", "ref": "👥 Polecenia", "phone": "📱 Subskrypcja telefoniczna", "apps": "📲 Instaluj aplikacje", "sites": "🌐 Rejestracja na stronach", "wallet": "💳 Portfel", "withdraw": "💸 Wypłata", "watch": "▶️ Oglądaj i zarabiaj", "terms": "📜 Regulamin", "menu": "Menu ⚙️", "welcome": "Witaj", "bal": "Aktualne saldo TRX", "pend": "Oczekuje na weryfikację", "minline": "Minimalna wypłata: {n} TRX", "faqT": "❓ Ważne zasady i instrukcje", "faqD": "💸 **Wypłata:** Możesz wypłacić po osiągnięciu minimum i przyprowadzeniu 1 prawdziwego ukończonego poleconego.\n👥 **Polecenia:** Zarabiaj 3% dożywotnio z zarobków swoich poleconych.\n🚫 **Anulowanie ofert:** Jeśli anulujesz subskrypcję lub usuniesz aplikację, Twoje konto zostanie zawieszone. Aby je odblokować, musisz przyprowadzić 5 ukończonych poleconych LUB ukończyć nową udaną ofertę.", "refT": "👥 System poleceń (3%)", "refCnt": "Aktywne polecenia", "refD": "Udostępnij swój link i zarabiaj dożywotnio 3% zarobków poleconych. Polecenie liczy się dopiero po jednej udanej ofercie.", "copy": "Kopiuj link polecający 🔗", "copied": "Skopiowano! 📋", "noOffers": "Brak dostępnych ofert.", "go": "Start ✅", "reward": "Nagroda", "pendNote": "Dodawane po weryfikacji (24–72 godz.). Anulowanie = blokada konta.", "wDesc": "Wpisz adres swojego portfela TRX (TRC20):", "save": "Zapisz 💾", "change": "Zmień 🔄", "wSaved": "Zapisany adres:", "noAddr": "Nie dodano jeszcze adresu", "wdBtn": "Złóż wniosek o wypłatę 🚀", "wdInfo": "Wypłacane jest całe saldo. Wymagane minimum {n} TRX i jeden prawdziwy aktywny polecony.", "lang": "🌐 Język", "loading": "Ładowanie…", "c_auth": "Sesja wygasła. Zamknij aplikację i otwórz ją ponownie przez bota.", "c_banned": "Twoje konto zostało zablokowane za naruszenie regulaminu.", "c_vpn": "Wykryto VPN/proxy. Wyłącz je i użyj danych mobilnych.", "c_bad_address": "Nieprawidłowy adres TRX.", "c_ok_addr": "Adres zapisany 💾", "c_no_address": "Najpierw dodaj adres portfela TRX.", "c_min_balance": "Twoje saldo jest niższe niż minimalna wypłata.", "c_need_referral": "Potrzebujesz jednego prawdziwego poleconego, który ukończył pierwszą udaną ofertę.", "c_pending_exists": "Masz już oczekującą wypłatę.", "c_ok_withdraw": "Wniosek o wypłatę wysłany 🚀", "c_err": "Coś poszło nie tak. Spróbuj ponownie."}
}

AD_UI = {
    "en": {"adInterT": "Rewarded video ad", "adPopT": "Quick rewarded ad", "adWatch": "Watch ad", "adWait": "Next ad in {s}s", "adStepOf": "Stage {a} of {b}", "adProgress": "{v} / {t} views", "adEarned": "Accumulated earnings: {r} TRX", "adDoneHint": "Stage complete! Collect your balance to continue.", "adCollect": "Collect your balance", "adLockedT": "All stages completed", "adLockedD": "You can watch ads again in:", "c_ok_collect": "Added to your balance: +{r} TRX 🎉", "c_ad_cooldown": "Please wait a little before the next ad.", "c_ad_early": "The ad wasn't completed, so it was not counted.", "c_ad_invalid": "The ad session expired. Please try again.", "c_ad_fail": "The ad could not be shown right now. Try again later.", "c_ad_sdk": "Ads are not available right now. Reload the app and try again.", "c_ad_locked": "Ads are locked until the timer ends.", "c_ad_collect": "Collect your balance first to continue.", "c_ad_notready": "This stage is not complete yet."},
    "ar": {"adInterT": "إعلان فيديو بمكافأة", "adPopT": "إعلان سريع بمكافأة", "adWatch": "شاهد الإعلان", "adWait": "الإعلان التالي بعد {s} ث", "adStepOf": "المرحلة {a} من {b}", "adProgress": "{v} / {t} مشاهدة", "adEarned": "الأرباح المتراكمة: {r} TRX", "adDoneHint": "اكتملت المرحلة! اجمع رصيدك للمتابعة.", "adCollect": "اجمع رصيدك", "adLockedT": "أنهيت جميع المراحل", "adLockedD": "ستتمكن من المشاهدة مجدداً خلال:", "c_ok_collect": "تمت إضافة {r} TRX إلى رصيدك 🎉", "c_ad_cooldown": "انتظر قليلاً قبل الإعلان التالي.", "c_ad_early": "لم يكتمل الإعلان، لذلك لم تُحسب المشاهدة.", "c_ad_invalid": "انتهت جلسة الإعلان. حاول مرة أخرى.", "c_ad_fail": "تعذّر عرض الإعلان الآن. حاول لاحقاً.", "c_ad_sdk": "الإعلانات غير متاحة حالياً. أعد فتح التطبيق وحاول مجدداً.", "c_ad_locked": "الإعلانات مقفلة حتى ينتهي العداد.", "c_ad_collect": "اجمع رصيدك أولاً للمتابعة.", "c_ad_notready": "المرحلة لم تكتمل بعد."},
    "es": {"adInterT": "Anuncio en vídeo con recompensa", "adPopT": "Anuncio rápido con recompensa", "adWatch": "Ver anuncio", "adWait": "Próximo anuncio en {s} s", "adStepOf": "Etapa {a} de {b}", "adProgress": "{v} / {t} vistas", "adEarned": "Ganancias acumuladas: {r} TRX", "adDoneHint": "¡Etapa completada! Recoge tu saldo para continuar.", "adCollect": "Recoger saldo", "adLockedT": "Completaste todas las etapas", "adLockedD": "Podrás ver anuncios de nuevo en:", "c_ok_collect": "Añadido a tu saldo: +{r} TRX 🎉", "c_ad_cooldown": "Espera un poco antes del siguiente anuncio.", "c_ad_early": "El anuncio no se completó, por lo que no se contó.", "c_ad_invalid": "La sesión del anuncio expiró. Inténtalo de nuevo.", "c_ad_fail": "No se pudo mostrar el anuncio ahora. Inténtalo más tarde.", "c_ad_sdk": "Los anuncios no están disponibles ahora. Recarga la app e inténtalo de nuevo.", "c_ad_locked": "Los anuncios están bloqueados hasta que termine el temporizador.", "c_ad_collect": "Recoge tu saldo primero para continuar.", "c_ad_notready": "Esta etapa aún no está completa."},
    "de": {"adInterT": "Video-Werbung mit Belohnung", "adPopT": "Kurzwerbung mit Belohnung", "adWatch": "Werbung ansehen", "adWait": "Nächste Werbung in {s} s", "adStepOf": "Stufe {a} von {b}", "adProgress": "{v} / {t} Aufrufe", "adEarned": "Gesammelte Einnahmen: {r} TRX", "adDoneHint": "Stufe abgeschlossen! Hole dir dein Guthaben, um fortzufahren.", "adCollect": "Guthaben einsammeln", "adLockedT": "Alle Stufen abgeschlossen", "adLockedD": "Du kannst wieder Werbung ansehen in:", "c_ok_collect": "Deinem Guthaben gutgeschrieben: +{r} TRX 🎉", "c_ad_cooldown": "Bitte warte kurz bis zur nächsten Werbung.", "c_ad_early": "Die Werbung wurde nicht abgeschlossen und deshalb nicht gezählt.", "c_ad_invalid": "Die Werbesitzung ist abgelaufen. Bitte versuche es erneut.", "c_ad_fail": "Die Werbung konnte gerade nicht angezeigt werden. Versuche es später erneut.", "c_ad_sdk": "Werbung ist derzeit nicht verfügbar. Lade die App neu und versuche es erneut.", "c_ad_locked": "Werbung ist gesperrt, bis der Timer abläuft.", "c_ad_collect": "Hole zuerst dein Guthaben, um fortzufahren.", "c_ad_notready": "Diese Stufe ist noch nicht abgeschlossen."},
    "fr": {"adInterT": "Vidéo publicitaire récompensée", "adPopT": "Pub rapide récompensée", "adWatch": "Regarder la pub", "adWait": "Prochaine pub dans {s} s", "adStepOf": "Étape {a} sur {b}", "adProgress": "{v} / {t} vues", "adEarned": "Gains accumulés : {r} TRX", "adDoneHint": "Étape terminée ! Récupérez votre solde pour continuer.", "adCollect": "Récupérer mon solde", "adLockedT": "Toutes les étapes sont terminées", "adLockedD": "Vous pourrez revoir des pubs dans :", "c_ok_collect": "Ajouté à votre solde : +{r} TRX 🎉", "c_ad_cooldown": "Patientez un peu avant la prochaine pub.", "c_ad_early": "La pub n'a pas été terminée, elle n'est donc pas comptée.", "c_ad_invalid": "La session publicitaire a expiré. Réessayez.", "c_ad_fail": "La pub n'a pas pu s'afficher pour le moment. Réessayez plus tard.", "c_ad_sdk": "Les pubs ne sont pas disponibles pour le moment. Rechargez l'app et réessayez.", "c_ad_locked": "Les pubs sont verrouillées jusqu'à la fin du minuteur.", "c_ad_collect": "Récupérez d'abord votre solde pour continuer.", "c_ad_notready": "Cette étape n'est pas encore terminée."},
    "ru": {"adInterT": "Видеореклама с наградой", "adPopT": "Быстрая реклама с наградой", "adWatch": "Смотреть рекламу", "adWait": "Следующая реклама через {s} с", "adStepOf": "Этап {a} из {b}", "adProgress": "{v} / {t} просмотров", "adEarned": "Накопленный заработок: {r} TRX", "adDoneHint": "Этап завершён! Заберите баланс, чтобы продолжить.", "adCollect": "Забрать баланс", "adLockedT": "Все этапы пройдены", "adLockedD": "Снова смотреть рекламу можно через:", "c_ok_collect": "Добавлено на баланс: +{r} TRX 🎉", "c_ad_cooldown": "Подождите немного перед следующей рекламой.", "c_ad_early": "Реклама не была досмотрена, поэтому просмотр не засчитан.", "c_ad_invalid": "Сессия рекламы истекла. Попробуйте ещё раз.", "c_ad_fail": "Не удалось показать рекламу. Попробуйте позже.", "c_ad_sdk": "Реклама сейчас недоступна. Перезапустите приложение и попробуйте снова.", "c_ad_locked": "Реклама заблокирована до конца таймера.", "c_ad_collect": "Сначала заберите баланс, чтобы продолжить.", "c_ad_notready": "Этот этап ещё не завершён."},
    "pt": {"adInterT": "Anúncio em vídeo com recompensa", "adPopT": "Anúncio rápido com recompensa", "adWatch": "Assistir anúncio", "adWait": "Próximo anúncio em {s} s", "adStepOf": "Etapa {a} de {b}", "adProgress": "{v} / {t} visualizações", "adEarned": "Ganhos acumulados: {r} TRX", "adDoneHint": "Etapa concluída! Colete seu saldo para continuar.", "adCollect": "Coletar saldo", "adLockedT": "Todas as etapas concluídas", "adLockedD": "Você poderá assistir anúncios novamente em:", "c_ok_collect": "Adicionado ao seu saldo: +{r} TRX 🎉", "c_ad_cooldown": "Aguarde um pouco antes do próximo anúncio.", "c_ad_early": "O anúncio não foi concluído, então não foi contado.", "c_ad_invalid": "A sessão do anúncio expirou. Tente novamente.", "c_ad_fail": "Não foi possível exibir o anúncio agora. Tente mais tarde.", "c_ad_sdk": "Os anúncios não estão disponíveis agora. Recarregue o app e tente novamente.", "c_ad_locked": "Os anúncios estão bloqueados até o fim do cronômetro.", "c_ad_collect": "Colete seu saldo primeiro para continuar.", "c_ad_notready": "Esta etapa ainda não foi concluída."},
    "nl": {"adInterT": "Videoadvertentie met beloning", "adPopT": "Snelle advertentie met beloning", "adWatch": "Advertentie bekijken", "adWait": "Volgende advertentie over {s} s", "adStepOf": "Fase {a} van {b}", "adProgress": "{v} / {t} weergaven", "adEarned": "Opgebouwde winst: {r} TRX", "adDoneHint": "Fase voltooid! Haal je saldo op om door te gaan.", "adCollect": "Saldo ophalen", "adLockedT": "Alle fases voltooid", "adLockedD": "Je kunt weer advertenties bekijken over:", "c_ok_collect": "Toegevoegd aan je saldo: +{r} TRX 🎉", "c_ad_cooldown": "Wacht even voor de volgende advertentie.", "c_ad_early": "De advertentie is niet voltooid en telt dus niet mee.", "c_ad_invalid": "De advertentiesessie is verlopen. Probeer het opnieuw.", "c_ad_fail": "De advertentie kon nu niet worden getoond. Probeer het later opnieuw.", "c_ad_sdk": "Advertenties zijn nu niet beschikbaar. Laad de app opnieuw en probeer het nog eens.", "c_ad_locked": "Advertenties zijn vergrendeld tot de timer afloopt.", "c_ad_collect": "Haal eerst je saldo op om door te gaan.", "c_ad_notready": "Deze fase is nog niet voltooid."},
    "pl": {"adInterT": "Reklama wideo z nagrodą", "adPopT": "Szybka reklama z nagrodą", "adWatch": "Obejrzyj reklamę", "adWait": "Następna reklama za {s} s", "adStepOf": "Etap {a} z {b}", "adProgress": "{v} / {t} wyświetleń", "adEarned": "Zgromadzone zarobki: {r} TRX", "adDoneHint": "Etap ukończony! Odbierz saldo, aby kontynuować.", "adCollect": "Odbierz saldo", "adLockedT": "Wszystkie etapy ukończone", "adLockedD": "Reklamy będzie można obejrzeć ponownie za:", "c_ok_collect": "Dodano do salda: +{r} TRX 🎉", "c_ad_cooldown": "Poczekaj chwilę przed kolejną reklamą.", "c_ad_early": "Reklama nie została ukończona, więc nie została zaliczona.", "c_ad_invalid": "Sesja reklamy wygasła. Spróbuj ponownie.", "c_ad_fail": "Nie udało się teraz wyświetlić reklamy. Spróbuj później.", "c_ad_sdk": "Reklamy są obecnie niedostępne. Odśwież aplikację i spróbuj ponownie.", "c_ad_locked": "Reklamy są zablokowane do końca odliczania.", "c_ad_collect": "Najpierw odbierz saldo, aby kontynuować.", "c_ad_notready": "Ten etap nie został jeszcze ukończony."},
}
for _l, _d in AD_UI.items():
    UI[_l].update(_d)
AD_UI2 = {
    'en': {"adInterT": 'Watch to earn', "adPopT": 'Watch to earn', "adLockedT": 'Stage completed ✓', "adLockedD": 'Renews in 24 hours:', "adClosedT": 'Opens after you finish and collect the previous stage.', "c_ad_closed": 'Finish and collect the previous stage first.'},
    'ar': {"adInterT": 'شاهد لتربح', "adPopT": 'شاهد لتربح', "adLockedT": 'اكتملت هذه المرحلة ✓', "adLockedD": 'سوف تتجدد بعد 24 ساعة:', "adClosedT": 'تفتح بعد أن تُنهي المرحلة السابقة وتجمع رصيدها.', "c_ad_closed": 'أنهِ المرحلة السابقة واجمع رصيدها أولاً.'},
    'es': {"adInterT": 'Mira y gana', "adPopT": 'Mira y gana', "adLockedT": 'Etapa completada ✓', "adLockedD": 'Se renueva en 24 horas:', "adClosedT": 'Se abre cuando termines y recojas la etapa anterior.', "c_ad_closed": 'Termina y recoge primero la etapa anterior.'},
    'de': {"adInterT": 'Ansehen und verdienen', "adPopT": 'Ansehen und verdienen', "adLockedT": 'Stufe abgeschlossen ✓', "adLockedD": 'Erneuert sich in 24 Stunden:', "adClosedT": 'Wird freigeschaltet, nachdem du die vorherige Stufe beendet und eingesammelt hast.', "c_ad_closed": 'Beende und sammle zuerst die vorherige Stufe ein.'},
    'fr': {"adInterT": 'Regardez pour gagner', "adPopT": 'Regardez pour gagner', "adLockedT": 'Étape terminée ✓', "adLockedD": 'Se renouvelle dans 24 heures :', "adClosedT": "S'ouvre après avoir terminé et récupéré l'étape précédente.", "c_ad_closed": "Terminez et récupérez d'abord l'étape précédente."},
    'ru': {"adInterT": 'Смотрите и зарабатывайте', "adPopT": 'Смотрите и зарабатывайте', "adLockedT": 'Этап завершён ✓', "adLockedD": 'Обновится через 24 часа:', "adClosedT": 'Откроется после завершения предыдущего этапа и сбора награды.', "c_ad_closed": 'Сначала завершите предыдущий этап и заберите награду.'},
    'pt': {"adInterT": 'Assista e ganhe', "adPopT": 'Assista e ganhe', "adLockedT": 'Etapa concluída ✓', "adLockedD": 'Renova em 24 horas:', "adClosedT": 'Abre depois de concluir e coletar a etapa anterior.', "c_ad_closed": 'Conclua e colete primeiro a etapa anterior.'},
    'nl': {"adInterT": 'Kijk en verdien', "adPopT": 'Kijk en verdien', "adLockedT": 'Fase voltooid ✓', "adLockedD": 'Wordt over 24 uur vernieuwd:', "adClosedT": 'Opent nadat je de vorige fase hebt voltooid en opgehaald.', "c_ad_closed": 'Voltooi en haal eerst de vorige fase op.'},
    'pl': {"adInterT": 'Oglądaj i zarabiaj', "adPopT": 'Oglądaj i zarabiaj', "adLockedT": 'Etap ukończony ✓', "adLockedD": 'Odnowi się za 24 godziny:', "adClosedT": 'Otworzy się po ukończeniu i odebraniu poprzedniego etapu.', "c_ad_closed": 'Najpierw ukończ i odbierz poprzedni etap.'},
}
for _l, _d in AD_UI2.items():
    UI[_l].update(_d)
AD_UI3 = {
    'en': {"wdInfo": 'Your whole balance is withdrawn, whatever the amount. Requires one real active referral.', "c_min_balance": 'You have no balance to withdraw.'},
    'ar': {"wdInfo": 'يتم سحب كامل رصيدك مهما كان مقداره. الشرط: إحالة حقيقية نشطة.', "c_min_balance": 'ليس لديك رصيد للسحب.'},
    'es': {"wdInfo": 'Se retira todo tu saldo, sea cual sea el importe. Requiere un referido real activo.', "c_min_balance": 'No tienes saldo para retirar.'},
    'de': {"wdInfo": 'Dein gesamtes Guthaben wird ausgezahlt, egal wie hoch. Erfordert eine echte aktive Empfehlung.', "c_min_balance": 'Du hast kein Guthaben zum Auszahlen.'},
    'fr': {"wdInfo": 'Tout votre solde est retiré, quel que soit le montant. Il faut un vrai filleul actif.', "c_min_balance": "Vous n'avez aucun solde à retirer."},
    'ru': {"wdInfo": 'Выводится весь баланс, независимо от суммы. Нужен один реальный активный реферал.', "c_min_balance": 'У вас нет средств для вывода.'},
    'pt': {"wdInfo": 'Todo o seu saldo é sacado, qualquer que seja o valor. Exige um indicado real ativo.', "c_min_balance": 'Você não tem saldo para sacar.'},
    'nl': {"wdInfo": 'Je hele saldo wordt opgenomen, ongeacht het bedrag. Vereist één echte actieve referral.', "c_min_balance": 'Je hebt geen saldo om op te nemen.'},
    'pl': {"wdInfo": 'Wypłacane jest całe saldo, niezależnie od kwoty. Wymagany jeden prawdziwy aktywny polecony.', "c_min_balance": 'Nie masz salda do wypłaty.'},
}
for _l, _d in AD_UI3.items():
    UI[_l].update(_d)

LANG_NAMES = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English", "es": "🇪🇸 Español", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français", "ru": "🇷🇺 Русский", "pt": "🇧🇷 Português", "nl": "🇳🇱 Nederlands", "pl": "🇵🇱 Polski"}

MSG = {
    "ar": {"banned_start": "🚫 تم حظر حسابك.", "reversed": "🚫 تم إيقاف حسابك لأنك ألغيت اشتراكاً أو عرضاً. لفتح الحساب، يجب أن تجلب 5 إحالات مكتملة.", "paid": "✅ تم دفع {amt} TRX إلى محفظتك.\n{note}", "rejected": "❌ تم رفض طلب السحب #{id} وأُعيد الرصيد لحسابك.\n{note}"},
    "en": {"banned_start": "🚫 Your account has been banned.", "reversed": "🚫 Your account was suspended because you cancelled an offer. To unlock it, you must bring 5 completed referrals.", "paid": "✅ {amt} TRX has been sent to your wallet.\n{note}", "rejected": "❌ Withdrawal request #{id} was rejected and the balance was returned to your account.\n{note}"},
    "es": {"banned_start": "🚫 Tu cuenta ha sido bloqueada.", "reversed": "🚫 Tu cuenta fue suspendida porque cancelaste una oferta. Para desbloquearla, debes traer 5 referidos completados.", "paid": "✅ Se enviaron {amt} TRX a tu billetera.\n{note}", "rejected": "❌ La solicitud de retiro #{id} fue rechazada y el saldo volvió a tu cuenta.\n{note}"},
    "de": {"banned_start": "🚫 Dein Konto wurde gesperrt.", "reversed": "🚫 Dein Konto wurde gesperrt, weil du ein Angebot abgebrochen hast. Um es zu entsperren, musst du 5 abgeschlossene Empfehlungen bringen.", "paid": "✅ {amt} TRX wurden an deine Wallet gesendet.\n{note}", "rejected": "❌ Auszahlungsantrag #{id} wurde abgelehnt und das Guthaben wurde deinem Konto gutgeschrieben.\n{note}"},
    "fr": {"banned_start": "🚫 Votre compte a été banni.", "reversed": "🚫 Votre compte a été suspendu car vous avez annulé une offre. Pour le débloquer, vous devez apporter 5 filleuls complétés.", "paid": "✅ {amt} TRX ont été envoyés à votre portefeuille.\n{note}", "rejected": "❌ La demande de retrait #{id} a été refusée et le solde a été restitué à votre compte.\n{note}"},
    "ru": {"banned_start": "🚫 Ваш аккаунт заблокирован.", "reversed": "🚫 Ваш аккаунт заблокирован, потому что вы отменили предложение. Чтобы разблокировать его, вы должны привлечь 5 завершенных рефералов.", "paid": "✅ {amt} TRX отправлены на ваш кошелёк.\n{note}", "rejected": "❌ Заявка на вывод #{id} отклонена, баланс возвращён на ваш аккаунт.\n{note}"},
    "pt": {"banned_start": "🚫 Sua conta foi banida.", "reversed": "🚫 Sua conta foi suspensa porque você cancelou uma oferta. Para desbloquear, você deve trazer 5 indicados concluídos.", "paid": "✅ {amt} TRX foram enviados para sua carteira.\n{note}", "rejected": "❌ O pedido de saque #{id} foi recusado e o saldo voltou para sua conta.\n{note}"},
    "nl": {"banned_start": "🚫 Je account is geblokkeerd.", "reversed": "🚫 Je account is geblokkeerd omdat je een aanbieding hebt geannuleerd. Om het te deblokkeren, moet je 5 voltooide referrals aanbrengen.", "paid": "✅ {amt} TRX is naar je wallet gestuurd.\n{note}", "rejected": "❌ Opnameverzoek #{id} is afgewezen en het saldo is teruggestort op je account.\n{note}"},
    "pl": {"banned_start": "🚫 Twoje konto zostało zablokowane.", "reversed": "🚫 Twoje konto zostało zawieszone, ponieważ anulowałeś ofertę. Aby je odblokować, musisz przyprowadzić 5 ukończonych poleconych.", "paid": "✅ {amt} TRX zostało wysłane do Twojego portfela.\n{note}", "rejected": "❌ Wniosek o wypłatę #{id} został odrzucony, a saldo wróciło na Twoje konto.\n{note}"}
}

def user_lang(conn, uid):
    r = conn.execute("SELECT lang FROM users WHERE user_id=?", (uid,)).fetchone()
    l = (r["lang"] if r else "") or "en"
    return l if l in MSG else "en"

def msg_for(lang, key, **kw):
    return MSG.get(lang, MSG["en"])[key].format(**kw)

@server.route("/api/lang", methods=["POST"])
@auth
def api_lang():
    lang = str((request.get_json(silent=True) or {}).get("lang", ""))[:2]
    if lang in MSG:
        with tx() as c:
            ensure_user(c, g.user["id"], g.user.get("username") or "")
            c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, g.user["id"]))
    return jsonify(success=True)

# ======================================================================
# صفحة التطبيق المصغر (HTML)
# ======================================================================
@server.route("/webapp")
def webapp():
    terms = {l: {"title": TERMS_TITLE[l], "sections": terms_sections(l)} for l in LANGS}
    page = (WEBAPP_HTML
            .replace("__UI__", json.dumps(UI, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__TERMS__", json.dumps(terms, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__LANG_NAMES__", json.dumps(LANG_NAMES, ensure_ascii=False))
            .replace("__AD_ZONE__", MONETAG_ZONE).replace("__OC_SPOT__", OC_SPOT)
            .replace("__AD_SDK__", '<script src="%s" data-zone="%s" data-sdk="show_%s"></script>' % (html.escape(MONETAG_SDK_URL, quote=True), MONETAG_ZONE, MONETAG_ZONE)
                     + '<script src="%s"></script>' % html.escape(OC_SDK_URL, quote=True)))
    resp = Response(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp

# ======================================================================
# بوت تيليجرام
# ======================================================================
@server.route("/" + TOKEN, methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return "OK", 200

@bot.message_handler(commands=["start"])
def start(message):
    try:
        uid = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or ""
        referrer = None
        parts = (message.text or "").split()
        if len(parts) > 1 and parts[1].isdigit():
            referrer = int(parts[1])
        
        with tx() as c:
            u = ensure_user(c, uid, username, referrer)
            saved_lang = u["lang"]
            if saved_lang in HEADS:
                lang = saved_lang
            else:
                lang = (message.from_user.language_code or "en")[:2].lower()
                if lang not in HEADS:
                    lang = "en"
                c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
                
        if u["banned"]:
            if u["ban_reason"] == 'offer_reversed':
                msg = f"🚫 حسابك موقوف بسبب إلغاء عرض سابق.\n\nلفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً).\n\n🔗 رابط الإحالة الخاص بك:\nhttps://t.me/{bot_username()}?start={uid}"
                bot.reply_to(message, msg)
            else:
                bot.reply_to(message, msg_for(lang, "banned_start"))
            return
            
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            AGREE_BTN[lang], web_app=telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")))
        bot.reply_to(message, terms_html(lang), parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

def is_admin(m):
    return ADMIN_ID and m.from_user.id == ADMIN_ID

@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        return
    with tx() as c:
        rows = c.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY id LIMIT 20").fetchall()
    if not rows:
        bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅")
        return
    bot.reply_to(m, "\n\n".join(f"#{r['id']} | user {r['user_id']} | {r['amount'] / MICRO:.2f} TRX\n{r['address']}" for r in rows))

@bot.message_handler(commands=["paid", "reject"])
def cmd_process(m):
    if not is_admin(m):
        return
    args = (m.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(m, "الاستخدام: /paid 12 [رقم العملية]  أو  /reject 12")
        return
    wid, paid = int(args[1]), args[0].startswith("/paid")
    note = " ".join(args[2:])
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            bot.reply_to(m, "الطلب غير موجود أو تمت معالجته.")
            return
        lang = user_lang(c, w["user_id"])
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?", ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid:
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")
    try:
        if paid:
            bot.send_message(w["user_id"], msg_for(lang, "paid", amt=f"{w['amount'] / MICRO:.2f}", note=note))
        else:
            bot.send_message(w["user_id"], msg_for(lang, "rejected", id=wid, note=note))
    except Exception:
        pass

@bot.message_handler(commands=["stats"])
def cmd_stats(m):
    if not is_admin(m):
        return
    with tx() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        banned = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
        pending = c.execute("SELECT COUNT(*) FROM transactions WHERE status='pending'").fetchone()[0]
        wd = c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'").fetchone()[0]
    bot.reply_to(m, f"👤 المستخدمون: {users}\n🚫 المحظورون: {banned}\n⏳ عمليات قيد التحقق: {pending}\n💸 سحوبات معلقة: {wd}")

@bot.message_handler(commands=["resetads"])
def cmd_resetads(m):
    """للأدمن: /resetads يصفّر مراحل الإعلانات وعدّاداتها لكل المستخدمين، و /resetads 123456 لمستخدم واحد."""
    if not is_admin(m):
        return
    args = (m.text or "").split()
    uid = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    q1 = "UPDATE ad_stage SET views=0, earned=0, locked_until=0, opened=CASE WHEN stage=0 THEN 1 ELSE 0 END"
    q2 = "UPDATE ad_progress SET last_view=0"
    with tx() as c:
        if uid:
            c.execute(q1 + " WHERE user_id=?", (uid,)); c.execute(q2 + " WHERE user_id=?", (uid,))
        else:
            c.execute(q1); c.execute(q2)
    bot.reply_to(m, "تم تصفير الإعلانات " + ("للمستخدم %d" % uid if uid else "لجميع المستخدمين") + " ✅")

init_db()

if os.environ.get("RUN_RELEASE_LOOP", "1") == "1":
    threading.Thread(target=_release_loop, daemon=True).start()

if RENDER_URL and os.environ.get("AUTO_WEBHOOK", "1") == "1":
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    except Exception as e:
        print("set_webhook error:", e, flush=True)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
