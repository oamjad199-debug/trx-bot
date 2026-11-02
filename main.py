import os
import re
import zlib
import base64
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
_WEBAPP_Z = """
eNrdfc2T20iW311/BVRaCUQLZBH8LlIorVrSzMijljpa1T0fNbUVIAEWMUUSXABVrGoWD7thOxz2wSdHOMK++bCzEd6wves52j5M
7L3n1nPdv8S/9zIBJD5YVeqZjW47FEUSifx4+fJ958vUs4ev3r88+sXnr7VZvJgfPnhGX9rcWZ7Ze064p7l+aO+F8XyPXnmOi6+F
FzvaZOaEkRfbe18e/ag+2EuKl87Cs/cufW+9CsJ4T5sEy9hbotrad+OZ7XqX/sSr84Op+Us/9p15PZo4c8+2Gs1CN/HMW3j1STAP
QqWnR80e/vGQc395roXe3N5bhR4qLL0JxpyF3tTem8XxKhru70/RLmqcBcHZ3HNWftSYBIu07d1V9ydR1Ho+dRb+/Np+6fhhMFyf
zeI/7zSbox7++vgbNJtPZI3PnGUYrLx8HXrv+tFq7lzb0dpZ7QmYo/h67kUzz4sJntiP597h0Rc/11474fLZvnh+8CyahP4q1qJw
kgEae3PvLHQWjSA82/91lD7X19647qxWjV9He4fP9kXTwwenpy9enX549dPTU3RHgx4+0IZhEMSben18NpQIHdXrZ8HcHT6adifd
Tks+WnieTq1x8ro9fDQZHLQsRz5HwTRGFdc7cKhK7F3RY29qeR08Li5iDz0eOAftAT0D6d4wPBs7tVana1oHfbPXMxutlrF9oH2y
IfDP/bgeO6v6zD+bzfEXi/UfxqGzjFZOCBIYjYOreuR/7S/PhuMgdL2wjhL0QKRrjgP3erNwwjN/OWyikJ9pZetiiYY6r6Ju6nKt
dPPImQULx3wRghjNCOPUIy/0pyMx8qUT1sTEjNHKcV0a1uqurjTx0RysrkYLf1mfeQTu0Go2L2ejsTM5PwuDi6U7DB2XiPyMvgF9
zWo1H2s9/Dmx1sVX3Wo+Nks4sfqGqcyZGhhmsasBmndFTxj2MX/IrppN0+r0zBZ11azoSsxqfGYooNadOHYmswUqDaf+leeOgksv
nM6Ddf1qOPNd11tKhA6HY28ahN5GcuVwb2+0CiKwc7CUTf0lxMOwiWIfVcK6d4l60XAZLL3R13V/6XpXeBusnIkfXw8bfRUOf+Gc
eWXENXqEcP6kGbcea61WBer6BiElN+VuqwJ7VqPF/bVEf/0BENhJ+ut2zVbHMq1Bx2z07t3hgDsciA4H6LA7qACw2/1uELaxxP1W
FYT375Bplj+J/LqPtU4V9XW+I4SY8UFVfzu6GzlLLDUTjQuGw5r2Is1zIg/0UQ8uYmiIKSkJT3PmoKGlE3sgwAbpIS80H629OSS0
Zz4ifbNJ6Q/CFX1eZmRmZY2yWlHsT86vR3GwAhkmNbvNkRTUw+ncuxo5EEHLOgBYRMOJR3Q8+vUFWk6v6wnlYz7QaGMvXnveciQF
T51lg/i0gJtMcLSk4MhJCEJXz+yZAxBvxxglcpCquBBR9alP0x+O5xdhzQL5C6bd9SoRiXEcLIYWxouCue9qguNJAhsZPrRZa0Mz
HVoJ6M0Ribo6zzyZM4tPSFxvSEOIx7UQd6T/5l5MHE6YoDk2Ovnp0ZBOqNDMoOl6Z1ICsY4xlAeD5JPy3DbyCJEiYjL3V0OCdFRZ
mKoSmgtwNC+rEUICRN1FfRwvN2yRDNs0OynH+bfEJUF+EfHiyaJqvJYWVeWBZt/IaRSerIraA/Q+uQgj1JBCMyXGs9B3R/gFSssR
I81hHpwFu+C/o33SXIsuz5IumkoX9FsSGBNbNHPcYF1rak2NZFyVYCPaShhzU6akhMjQA6iEl4BMhI2CBkKyiieuYIwIwamObfSp
6cQJ3Qq2l2MwqzUzziuvZ4vmV4axtMI52+MWuu4xXWfSWf7RyleVtgxDk9CRAWMW+3vUdJvjZt+U37dXttrd/ODQ/Fa7yWtiVtFi
teBvdwBUZlTdIYqau0WReEWGGtMMVpyKNCIpQTdNk/5BMyhKIPQjT4PyEUoAcMSzZJ21WXujEM8gEUOZVCrxFjUd+2cKbbWL0guW
eUIuA6YWuDvwIQiWeRzeQ4iRcdyfTE1pNJNGNaWB/M8ktnYxJJN7eT0FR0Lah0EFqyT2nbTudrEOmzX8UcFEnTwTRbETxt+dhwQZ
P2oBgc2BBhJ9BNo/aHa1DiypR60xDNsDtnM/kh3aLdPqgt4OqtgBFrLWrrLUYPmJsRSWyBM1YaXTKRB1D4PQmuB91aI05etOs+ot
gCmxRJEjaDlvtcGdMdAOwcn2TR0aFUoajlodTD8Sgr7TfZzI+RY8khEvEPpbwDOMYWiBwoFB47bFOmAWUFa2wjK1ejnnQ51aBItp
pfWSyRVtvmyezhQEf/s0xZysA0V7iYeQfwMDRKWEi36zRMIwTW9z2CZ+OJl7ZeJoDQp+1eBxymuHn9xtj4ZBHRBtcgbn7dZlhTma
E1gsLGf+SuryTkvR5VZp2v2CFeqtPMAJhqpeZ5XArYEB+kX3OQSQ1IARY+zixkfTMcIETfPR+GDQs8Y5/cDuolZkGlVftphraIxB
SYewqAckOUOCZlwwTdvk+ZQ0QNkqS93Sg266VnNn7M2lDqKFU2zhouHyaHKAKTolw7gnTB5nEW92uhljsALhb3TmrEgpFVSSlNAs
oFnmyw6x8BehOvv7TbQAodofPupLpUempmKPeavMuqfGHHvNTGO2vjeN2akSvx2hMFdhcLaRE+uXWOfgoMKDy1t3A6OkXUu8SoNo
fkoL43kwOR9lcaTHd4xazacSmQmCTRm/K1hjuwyGniE0gRBdLEfg3luRNrkY+xNIoq99L6w1WmYDzip0aoqsenwVf4wsUxipn+cj
K+Ojcd/p9x11CG28qTT01rNgc5frThxFVqg6NhFBYuiIgszJE8+pCVPW1J2c/9bO4PYG7mQ8YFa63OVYlXXQXd5ekfmUsTvZ2NbE
6jTb9zGyBGFk3FcgECFsy2pPiNvYR/B6kwOZPsCIC5TEHLe/WCzhNU9DDX9F7EsjM+lqkxqb7bLfPbiXibnDEb+/m9bb5aaV7bGi
QUZT0KKFM58XuLmSrnOOrSRGGa/pCgnM/Y1VeT6ocnEKyiEZ2l+yXGYIqDdamNafZq2AymWe0eijnsEhutrFfgM1FtYTurzKKy/E
QcqReDWi7y+hoP0/EUXkLfFdBKHIyNRw1hpWNzLlZBhiLikRT69AO4TSoTMhE3GTWeG8KVZrHPTSiF6l3KPGWsOfSCnTVaRMtyxl
rHsEhe42hZNYdKtbFYsms7gq4GCU16dC+Za0VGWgCfbn6FZ0KBGtlhIUa0kLTFSbj4txp1JkM2fetLsV0aIiGLQhJuxRhBXv9ril
40LKXtVKTZVPMokotk8Ka9op80sVd9zLNky0B88z83LZ2iyzAqIL99cz7MxLo4+cbal2eEfj0bSF8oFwtvMk0EtiD5X+V+I27IIQ
0a9dvNqKTGEY8m+5YvdyNsWegXCo+1UONS+nwsrn3vrntXqr+cc41MqMdjrUM/SndRqt3Q41TXGnqEGAOonhsdu89KIIxe2EnKFH
YLlt/vQrnvQfIhIs6XA69Q7GzRwdCtq/e/CDqdVqH5iPPMtyMQKH5PrT5rTl3U5aLWD4wOy3mK7vpCxhBvnL1UW8qWbiQWHfp4pv
8/q7LF2wfrxnznOvFDV/lCZUvehONqHhNJhcRJtdeqdsKLYrhXQv7fA4xG5TsJxfn2xS13pArrWLbA9/HolQftHEw/voYgGMXm+q
5Fu1LOtX+bnCg/A26xn4gL1db4hnRkjZstxh03fcyaRTUAmDbmIidVSPfNZJgtWWKG9VeRm3DdypNPcq/ZL8xt6sgw34MIrrwbQe
X6+8jdKGqUgFg026ALwW3s95sgrOU05NWd+b4Z7EdCUlt2TQO4BZxJubPG8ppTuZNcC/K5nyh2wgVRJ3kDd5lMBfS8Z0gvgq3enF
8omKTfkGrsZOt6VIicL+znstVKdo2fC6p4XeHCGbyI9GKgsug3XorJg5fcVzUt2XlLx447xZHYm5xYormzb33+IpuMlCkxkpywgT
r0hgzkUcZHvpKXM05e4JtwZSMM/NjoyZNEzcbWbpCEXlp9J7/46UgfbObTp6s03gaQTLPBUQrG7orNW0CQGqsIAY4LpcLQ9A1dtN
WqF0ApT8JilyoEbmm0qw4xYfMuco8sqm+UjXAs+Kaddot3YHqe4Tl7T62C9F2Exkw6WyVk6PRdfubAqBJsJgCSnMYy6lW/yRof48
y6lpJbmye+R/7MpDyHgmhVkbX6CfnNGn+CCqXYLoft+CPsyYkcVQXnNTvzSpCpNJAtwvWk0l/fFxvk5Zg1dI/LsFr9Uy7gj4to3R
vQOQCRoa0ha/cz1Gu22xOwVYVb6lWbUpaSRgqapE4Vv+ncm7tHZj6VzWqUlFdCuHksK0qxuKaZHth6zWyS7juqeQyUF1ps4/r7nM
1vIjQbRF8ciuIcMgth8lXzJ9w9ea1Die9lTzlpe1yJl6dbhyTl1IDlENxkAiRQ+w+nIBemr45uMS1ByeQYoydn6qdvLv5oR2GSUW
5ZqYfYjb3l3Za4PdKSODcsoIGc/t4u56X+yeUyynYm99wFS8HFfEXqT5892jl22F6HqcInGrWPwoOdWsjg4rGk6GFEWsYjnGn7/D
3rvTglX1ptqfwvjMcIrCFpVIw91LeXBVBjGLM/Avijf/AsEQLLYmAg8WC9ePyTPrGUY6xkekQZCDIhGmeAHl/QaZnaYV8hhv8YCZ
n/Mm+Z+fe9dT5OR7kUZh3800hJxInN/mqBIrnDW1jYO0nqXUI5ra5jvmDIoNoiyIcWxEPAqpHltaLvEIi+ZxsQ0FiahNL6lEMSy1
TafUhpNzxQwq4W4y0DsWmlaa+1t48JW0GvxuGM9RHcGei4nn1heB5FJ6NDafmJ8kS0q/RDgui3ERFh76Czpd4mBrVyHk/Jstb765
sBjOsr2lnlhUrVWV96c0yO+8dKscoKQ28H97ysHH7PogI5e2V1QPu5V3b9q79JpoTlZ7RdZlak/R5OWuS9YgP9udqXSich0+9V3S
Jc3TIxtdG9zZoZp+OlAYc/CR6acdacI4Lthzk89eS1Iv3Mk8iBBmTMNQvZZark6zvGppTWC5EOi7I8mwnGfx/22qIYWYQSHOeK6i
udtNesO8rmXEGaaEVJKuN3Uu5nESCF5dzCEyM67n5x8jEaG/M7StiCtRm2QcS7X7bydsu1XV25Vpesjxg4zBIStxoOrZvjwdR8dj
8OX6l9pk7kQRTm1xpj3OeGnaM+FNJW+S9PM9zXflEw4kLfcO/+k//vdn+6IuN5u1uAafCaOTXbMWF2Od0r4oj5vHoPLLM43ORHwa
XNl7HJ9FAL61p9Ey23skKGVN1AXmo+QBj4L4fixpj0c929OuLPSzp12Lr6uWvWfhib+ytjQw2EFDcIRPBqImPQu6wrk9EUfZ29/d
AlRSbMO0flsbq9BC5JapLZ7t5yeVTn1fnfszGbqbAGVWD+cNr8U3+rQ6NEYYnONM4kU4rz06M5ICEUez9xQQn60c5MwAb59ZPa33
ttWB8HmLn63e24H82ftlshZJd9WtLettq5k0t95aLfnbstIOktOQsgPQ4+UZ08Y+EQfRJSgxT48y3COILnk4rKgoghqinvzNXatV
iLjRWNJ1SsYsTUHH//k/pHQsqDWtkdIywylHl51TJbiGGVDya8Vv5OmCvZSLSDbTgoARwSM7zxxQdys5Q+qHOCQ/byoVGjkrTw5R
wryMYu3LN/bp6ZdvTk9N7ej1F599wBN/U8HbF+9+fPruxWevqTR7oFc4f/nL9+9e2zofxaSfp6e6qb1/efrh8/dHVCx/ongkh4rP
7DU8wGDdOEqOe/7MG79YrUZ41aANleuawb+9K6DQxcODGFslKABj/ISFzktiipouiUSHO8EvP00VQqnCduLEk1kNhthWwvHm3Zsj
G+1I0L5yYufmBha2fPdnNlB26GK3iA4NNs68+PXco5+fXr9xaz7sHFnx3Yuvfvr6F/YGBy29oU6fugk7cKjjQzdXM4ikoc5fuokD
rEMdH5FuwrRDOX3iwXGH+pqg0801Em0QK9XFN579eEYUihL5Szex9DBJdP7Stwkg73/0o9dfnP70zbtXH+zjZEQaDZ80Dj24+sno
QTL7l+/ffdBsbQPaZOA1vSxeweOtTk68pvIC+o1U6UtxiLkoNJICElATZ4WT1rQoueJfw31Myg9T6bBoawfaQb2Pz/6lZTktrSVS
Z+v49ZOu+lxvfQ3p8GwVzK+pP439UbDNAU5PojkJla78bJEYEyJENzFhWqEfxnw/Ywl4WW85Ha0j0oTrnXrnJz31Wetc8gQUSX4g
BHmf5XiH8ZD0iNkXe2zX241BP1cL47YbVjutZOGv3+h384iS9PgDwVXLwnp+1VfJgNAzszqXeRS0te6l1UlrAVitNbN6l/VuHgfQ
Wy2lFrzjWeey3vllAQkJE36/aGAiJ4PFagmLxTqQJktL2CzdSnYQPACzWrOIKfJTI431Q5lWR8ymJe2xZFYC5F21eqJS77Y61kD2
NMhPXkjn73f25CppsjmZY8JFFLBf0ZJq19xveCW+roVJptAwFncwazSt/NxI1/xwZtbPJtbnebV5Xm0xLwb91uqEme9Qn77u16Bd
rp/hkpX194tM1YZvSRu+JWz4ZpEcWo7VaYDb6SORa2RtFwuRt5XXG5AOM1Gm0JH7fQt/yLMzWOCJOIPa4tm0NFKc+GjnARbW0Q9F
uWNIqPJUw5ARc2n1iopJ1UEwa74aVBs21BtWUBsQAgY5iUcOHYu6thB9icRrV9fq52v1q4drkimGfwPtII9jukXn/y2G6DbaGn8I
owGua1MrFNarC+vlQo0Kv85Q8gBG+AOYSeJ2IQTRnPmHOAgRbyXH4Q0iiDWdXunGzU2tpngcXy5pk+zJk1JR4wIXtewqb1BfF+j9
dBK4HvrUnVA3GtEcNxBhKwlbDg/8ae3hl2+OqeKJIcCiSiOGMqJTkPYGJv/yYj43Y2ecOC6c/RGJYv79OgzFk5f+cH06SjecOghF
bVNv4vMXb169tTdOONS//Zs//Mtv/8e3v/3Dv/32v2n08Id/9Yd//e0/fPt33/5G+/Y3+Plfv/2bb/9ON73lUP9wMZkgF3OKnq9T
M2uJd/BvvvBiH4GNgC5I0n73t1d+jLttXHhNr8NpMEfGpj+ZIRAbnXlfO7M5fKVpKBv97m8159JD9BW9/+43cLDCi6H+zX/5/V99
83+++e3v/803/+ub/6198/e//3ff/P03v/3mf+IPBfDV4HZ9cCZixAU1BmQYcjlP4LwM5lqwOvOWQBaAXOHF58Hi+h//03zpe9r6
evWPf+0A2CBzyo7sc/uwlqzEkyfJr+PzE6zbl28a3hI/b27ORw+mF0sOmmqzGiL1Jm6sCSOz0Wic+25kbER3np16pBP4ybEnnVJq
gVXXNGwu1ETVc4QQtRr3cnOz2RpJF5c2l2HUEcdVQCnntm3rHHLQDc1r8K93dE/V5UjjOh6WOq3o4zKq8CdHn73lyukTKufr0vge
qmAk6ojLPfLRX2B8H6ETr3ZuXvJ+uEZzbEyxr1IzGpjCa9zVU5vYhxv0M7Ftojsj9OKLcIl+GrBskH1SmzSWoP4jJAI+nwwLaDlC
qOQd3tY+YKjlWW1iYNt5yxgS/Wi0yZ9ifBGd1WJjQ2BTGGEWrF/MvTA2NPUJNeQsnPRx+8CJrpcTLe0Jl2vVSPLwZU0GudYC68Eq
RoiAIxfRcKP/vP4GbF0nvtaHFIYw9Zdik69OE9I5SgB25hgx7sEKlvp2S9ADQur5oW1DCnoIESN2j1B0jPs+4lng2vrn7z8c6SMq
oXr2v/jw/l0jYiRg55zbCoxTPEWAFtrO2vFjbepReISBR3NjJBElXoYNAqKmRlHE+00kOFjIA5ME0lCHsAALbB8oKKYXnwHNLLFk
W+2opk9O9adcCClGzWidikidBKtrWtFaxBgl0AVUiKT5Zw4kbYOi/+MAqbaNNXafPVlbgVbM1bdnNZ3zdnVzc+nML7xhBLJIqYfw
k9CXb4z8hsjUqClVvCtv8jJA7i6q6ASZTvVCb4F4Y03glsjpiF/6nkszyiECQNZStpaIAFSIyQEm5r2hTpX0bcr96LWIk3nguJ9h
QDkxVy4i0Z++j899iHMQKOjFbcglMjYs+EEqtjsSP4Fx5q7Rlgh7kxW6DWVNRltwDcgtrFUszlkA4TPmhRHN8WTjb6RxpPQVR1cp
nCc7F+rDZnKRFK1EriBPJvML14u4U+416VfoJgGuWvQ6mUMGJLfahRjRz/NzRCBt/SkNkwrCEqrkmK78MXJcRCnn16iIHdKbGxZM
wA5LhXyT45NRAUaBUiaQLcuhBFiFOGiPJMHY5s9AFPwbup3p4q0fxRgYdAd5YIzwXsa4d1RQqU5dix09Sxq+tfNcne0D1Er3dlAv
wOLh7ik7m8ZIS6owBEodBSKulI1WVeNBNpXxhT933zmXNUW8QhDY6ANfRPT4AqC8fftyhspAtSAKSRLc5REyKBD93B0pNWWA9YSV
YNYoVVBE6Icbhdb86IXI/rIzVtCgMjViB65HkEnxApYX2wcZ19NWM6Rh0s1zXRPZZFAHumFKtAxrhn0omW5rJltB6I12G7K+ZP6Z
bqYKesgB32O0O9kaFQ23JumJ1VsoKUgvEdbm2tCdXNtgHG4VTJIp8zPkOWPCqQTjzYqhrmwit5rFIwLd+x9E7hq6GDEZS8FfTmTy
Xgni6mL4++QrDrKUf5msMLjPiQvIZQVrBfSyaQ70kmoTFr+h4AvahBSQUCpojCWdoZI39EBIbKQTzYTwGRqsnEY5VyLKuRImfeKM
VCrXROlGADDKBLYkkvfjX2PQBvaSo1q2hWM0Fs6qNrcPARa0vs/kKBQjLoxkOHHN5RxEzP2aWcvj+YmcW3Fl0IzLFWJPqrC0k6bx
p9geOj4WjseJecz7JfQtdz74Z7LlcXKSGNQpjdqRfSitu8hI2L22/xfHf/Gr1ebtFh/vtidP9y9M8E4D9RY1I9fHC3io1V2oPfwq
Qh9nopO0wq8ilJm6pnSs2CoXy/jLVc2DXxUoEipu2itkeCOHyFlOPJiu6xqoxL0IbQtb+YSuWtoH5d6QPSoNeVy9Gs8aONpQs8wa
0hqaxj7aoTVulq3zuxV6s+rnZttIbPAGbRZKk9I+f2Y9r8XBJx7gDX5EeZy1ljGcjlEmTARUMKCQ/vLCi+IXSWrCjyjloEawkOlc
w7A5VcVi+FPmG1USj0kOC3YiUTyuFsRY+1SM1oSQsQ/Ht4jG5RiCMbMvbLIwIB9R5Q7ZWBaM/k6ZeD9ZKKn+TmhpjhGIu3ZlH14d
N08AdDoB47kOwAn8DPZMaX4E6HzPXxXoIG+yQem1LmHeihiF4356EV0nBphYtZdv37/86emHr35s/7BjOqUIFQUBxe4GJQ90spBM
MrMfxsQ49HzF+xI0J2R2JBH/XhaIxhxllF8NX2GHyvqqr+zS4fDpZcVEpwt7mYqzp+8uFmOI/2XG8T0jlX/TMVWV4iWyb28jPZRa
LWpApfpxTW/oxrGFmAXJxLm3PItnh3bLeB4Nyx0gFJWGQmaLiATuMUssHHVBpCLab+MgjWGqRY+paL+H0uhxr3nC+imbGPqGJfGB
TkvUWqbeBG03CNU1sFMm371J9BYJnzbdOGQfCvHpXCE0xj8nnj+v0at67RXxI8viupQusOtfxDc32QvD2IeAbhqqkE/cACfxE9DK
dhKvhLuwsx7KPhNUXYj7sV+4kSo6g1tdFVikhvSXgh1uSpC4KSmAQc5PEa1VKUp2rpFzRUhCBJPPhUelOCaTDzOay0b08RBVpHNG
MROELIKpJnM6KGD50j1aOAhS6EkHPAoT0ufItUXWMPQC2SO1pbfW4B1RqkbknuuG1GAEQlYTxiGcjmL/tY3vDmV2CeJbDenrg7LT
CcSzMFhTrEeYrln4BzUauIR9WQsTE54mPpXTzs8rtPMTmdphPtRFgVqlasCWli7xk6zuOZIyKJZEPgaFlFz54yvf9QL5+wtvDcef
zFidrFd8hRdLekf0jm92s04aCPu4xBPJoMfLkzyIaYLYzY1q9oXG3U1Hsi1ZBTxVhO9w1yRahfLdNkHPw2k6b7k0NIcSspR3o6yp
UVwkhRCWuLaVqU2jxGwN97trN1i4CGmU5LFL0J/uwDvMApotahbmLuSEqRvQvGzioooUK6FhPNUxiDqPdCSlkCtFq4DgkJQn+Col
rGkt9ZJKbM8pPi/cGvIiTT9hJaGOE/ZQfAWCQQwtCAeBMplhdZLV8qP3EzsTXU+epD8bnO8dHfsnDWQyEXomqQChVs/vw7VDWYnG
z7PzJglynTruqeRcOYUt7xqykRGHcGI0yntN8mZFkYziKdEdx6UYia6rsZuoJBAdd1/ywoanN/S3WfTmYZTJxYUMNVLIMeLAC+BL
YpmK9B1pCtAKUEJSNqaLOEHdRrZOJCGCvzLuI19ESbHgkjTyKPsj+cIT5EFCu4ZtnxoF46IIE7m54bhbENIPhL84NQ+IpkdEtCPx
S8wDe0hyWTwCTkR39efesBDs5Z2hLPHtlBLfBCzq2k1xSwEtXm4dErYQSj7ZWMIZ2AxhiizYFWnDamEjZYWZI6SyiWEa4aBjg7+3
lUG3XHgtC6ypi+netpgcW4OIgwcp1zFn7N6l/Wg+FcHnOXnBd7PtR5D8rQiby+BAmcB3Yypb0eD8NOki81j1TbjF9tgC1UNWMUaG
wCSQLDng+8C4Yle9BHAQ1vgfPBTDyLFTqcY9PnTK4pL+XxVEXYEDx31DIZ4juFb89Hmwwm+WmY4UipnvGWFF80E82qSxjxF5r6W1
pZFrPT8uBp3EORlEhHikD/j9fprDuwO8+08ttWiMokLXhnEyPD5hL27MLhzPBqKb+S/bqEN9HNA4pcNMh81UshC2dkXF+IJpPjWi
ieMfYleBJpmGALXyrORBkTScVrgZQ3VDU9dRCSpq6UQYL2/Rm+diEfI1VsXgXa76q2L1Aoh8VgXa3MUeWp1/g1dMOBm1xPxX0ZW6
7ZmqLlozUYPMq4/Hqjhe8yfH6w607kLaS4biSL99noLEV5NYiSk1pVvEvipwRi5ytB/JQOQnlvB9staYtX0rQpi0y/gotqF7LysR
gTM4aE0bdVk4WZyh0p8C9Kf6Y4SEjdu6pes0RRdpUESIAryD7IpyLHoJfpSzVotjLhZIMBTWlBDsBkAcdUvWhf7LI9oELMviiO9q
89xsxZjDOf09pUJgVCHCXYv/CrGLnyAioiuLLxZrMrYr4lPQTuIoUUo9icrImo/TfRgKqmVacDKGyBypgE2SHTSxiZgbf207DdIa
h83nKVuKEmPYzIO63gkqX86VsLrIkx/qFmBfo1uG/2foMIfjCDheG0P5klpkU1uPM9WMHkZUoM41MdPXpZmuxzkfSBURqKVsj6Rq
j80poyhMSuto4sjcUMdpuZQhlMMeJL+Kt22usXtSH4NWzof8iarz9LYK1+k4U50CgRkI7I/QDgLpRng/tZrUe9UqNlXaD4XSvrl5
iOMRZaOHrFoc0sCBPzfb0k33yhFQDq8/8C5CEFJEUj9OxfWJnqV6YFskp4MRmc+IRfoxTxHUpsaYA4v1E0W4V0a9SRXMRXx7/szG
PfgJnIk5li6VfEG78YppozgGZO9JMjZUONd2kagFJHcigElMxQDIPEEBD7emkcpGJNuV6iRvo/5RYu4zW+Y6k9bZjt6YXWRrxfxc
MxbFRO2mNN5MDo5hf1bG3r568/pnH2zMhPZ1apeKFbewk/QDkzXQgtTPabLFA07epZIWjbEzp12T/XwToZqEGJFUDHetFDXn277B
DdjvSHtSN+Xk/9Vn1/Ca7C7YXF+mOzuI2yfPwZfg3/AlCFBYrpe7rAO6U13PYvild6TlhHbK61Bcb6+LUH6unG9/R32d/we9F1+8
S3VPZed8mbuQ65jszrrASk5DJkBchHIomM+oI1uTOVxar+NKjX5fzX1/vb0QVw7lKHwJCs8DVKmjhVldOR6u1a5YBCQQbE1JEfld
lZQ4UhOLjUYmad70IwGSexQsm2wIAplmRn/MXTspiG+g3kVC9FIiiW5lTrBEHekqEphe9KdM9vQSDr2xC/k7+oQ8fMlWRdZrcsPN
Kd91EEKO3Npnos74UmZxBcnQ2q9bxcE4fVSkRt7c8AMyI3dNxvHd07V7c9NMrXrByTRIyTTlG6JlDsEtx+JSSYx8TWpyy+4em3fF
LcfznRuOZO4XNxzP89uNsuZ8rFduPJ4r244pzRCQZTkkLp0sJJJVGdndwnXVckHEpZQZ9xZuy8tfEdmtuG2rcJVXk3sGKU2dvzyS
hLTalbRReYdl4Qa8wiWV+Wvp0wOx6ZivEm6l1QHJ7tBIOTxyhh7gnLUVPjhSJemqyCBPdWTDJ9QqZ1OVOHIr91Rb96j5Sh07n724
gEycntL/+GqS4/AeF5EOSeyk5IntkDSnJElm3Ga9VZjbedJOcy+zkQyGS6Q+ZsgVW0+1S5N2q9TEBzoN/VPv2k6IGa+VAPbELqE7
aZGJWWrzMIkeTe50iOjtuwCsnfWQ2yeTGcX36ImCY36WxZNs+OQz+8od5Sggs8fTgHS+eb7vhyqoMj6kPXmiPWQsyBiaEuc37jOP
ZfCe+8tNZJOgNgnMbTIWoGifDMZRinYuBTMVlUFqte9SZNygQs0GlUKRKKPCAMItnqILoQqCBhNIhfykqzbJenmqPw1koBMbNmzL
qN76LS6mSvlJOjhFhd4S2WvKA3ZWccFBkhAu91DopXhh6qdjKLNzSoHZ8gqcBandsE23Yh9OGuI+EspVNzQV/YKpRC7UTjN65kT2
w4cL2KpXCOW7FNpQ7dqVmu2MvVKd6tCxBQjYGSQSrizRj2Da6WYiTJSOMnmCUZ48eZhL31WTAMl1uUuScEy9lkZaMfWKThPzKUkR
ZvMpjRXn9ml2B9AZdkAhf+E+spXIpZMG/faWbN98brIaUmfE0f+WUQiZi+WvjJbTQm/NynlSzEIk/ukcoohwWEUvqPeyEpJ5cTt0
KBikPBINtP6A3l0x0PoVdpaoB2DFxAKlwjsxor+bekzT9HaZgvi/CvW8DZf6YXdovwT6fL0dGla5BlEmcI5RWh0ryd1RxJpZof2b
G5aZL8Sq3wUi9humwd3eieJISXMcRmyVGyUDiHmrTdyzS4aN/k///h+ARh75c9FRKbz4VB0jzcbBfwBV8IiqRGFIFtkOxt3Nednt
FJttGmlbMENILnueMFNGLsNde0wph4kYhMTzpxApisXB6dk5ikUEg64sSfwIfoAfcYu1EUtlwiORhcQ0kam4iPKkFO0264gUO8QF
yooKNisZ8EiOSk8bTRq8ihxleUHRPFsmc4yK0p7PECoZQkLsbdRwWvJDHvpqiNOG+BjtrgM6tzn9lpU8yPm5HsZzXQQbCUKkazIK
KMSRCwVJey2NBJ4YWTJ/dQuZbThSUvRH+TzRbCU4X5+C7lR/R7p+amnBVM7F3XinHHSTJtqjgBPtEfJYUridDKbkqF1jcipKYXTj
jAFdhfb8tpdDLW+n0eCCDksiUPgBCTS8qfogv/GyzcUJFp5iY93mCZWu+imbo2riAlAprw4qr0n6IsmfXXgcyXhOLsvTXBGl0t52
JCdLXzVEnK+RGv3ZK2kS8XuFeMiMRASacEHn3QzlrJGOy/RmOGT0INX1BIGope3Kb89EhMZ3lcm7jHAnk7ilbH8WL+aHD/4vvlxV
lw==
"""
WEBAPP_HTML = zlib.decompress(base64.b64decode("".join(_WEBAPP_Z.split()))).decode("utf-8")

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()   # رابط PostgreSQL الخارجي: يحفظ البيانات بعد كل نشر
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
WITHDRAW_HOURS = int(os.environ.get("WITHDRAW_HOURS", "48"))   # مهلة تنفيذ السحب يدوياً
ADMIN_TZ = int(os.environ.get("ADMIN_TZ_HOURS", "3"))          # فرق التوقيت لعرض الموعد (الأردن +3)
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "0"))
REQUIRE_REFERRAL = os.environ.get("REQUIRE_REFERRAL", "0") == "1"   # شرط الإحالة للسحب: ضع 1 لتفعيله
ADS_ENABLED = os.environ.get("ADS_ENABLED", "1") == "1"             # ضع 0 لإيقاف الإعلانات مؤقتاً
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
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "6154562") if ch.isalnum()) or "6154562"
AD_NETS = [x for x in dict.fromkeys(t.strip() for t in os.environ.get("AD_NET", "oc,mt").lower().split(",")) if x in ("mt", "oc")] or ["oc", "mt"]   # oc = Onclicka ، mt = Monetag (بالترتيب)
AD_STAGES = [{"fmt": n, "views": int(os.environ.get("AD_VIEWS", "10")), "reward": float(os.environ.get("AD_REWARD", "0.0005")), "min": 2} for n in AD_NETS]
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
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
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
        pwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        paidwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='paid'", (uid,)).fetchone()[0]
    return jsonify(
        success=True, pending_wd=pwd / MICRO, paid_wd=paidwd / MICRO, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO,
        pending=(pending + pwd) / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}",
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
    if kind == "ad" and ADS_ENABLED:
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
        if REQUIRE_REFERRAL and active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        now_ts = int(time.time())
        address = u["trx_address"]
        uname = u["username"] or ""
    if not ADMIN_ID:
        print("WARNING: ADMIN_ID غير مضبوط، لن يصلك إشعار السحب. استخدم /withdrawals", flush=True)
    else:
        fname = str(g.user.get("first_name") or "").strip() or "-"
        body = ("💸 طلب سحب جديد #%d\n\n👤 الاسم: %s\n🔗 اليوزر: %s\n🆔 الآيدي: %d\n💰 المبلغ: %.4f TRX\n📮 عنوان TRX:\n%s\n\n%s\n\n/paid %d  أو  /reject %d"
                % (wid, "%s", "%s", uid, amount / MICRO, "%s", wd_deadline(now_ts), wid, wid))
        try:
            bot.send_message(ADMIN_ID, body % (html.escape(fname), ("@" + html.escape(uname)) if uname else "-", "<code>" + html.escape(address) + "</code>"), parse_mode="HTML", reply_markup=wd_buttons(wid))
        except Exception as e:
            print("admin notify (html) failed:", e, flush=True)
            try:
                bot.send_message(ADMIN_ID, body % (fname, ("@" + uname) if uname else "-", address), reply_markup=wd_buttons(wid))
            except Exception as e2:
                print("admin notify failed:", e2, flush=True)
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
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
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
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
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
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
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

_UI_Z = """
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
"""
UI = json.loads(zlib.decompress(base64.b64decode("".join(_UI_Z.split()))).decode("utf-8"))

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
    'en': {"wdPending": 'Withdrawal request under review: {r} TRX', "wdInfo": 'Your whole balance is withdrawn, whatever the amount.', "c_min_balance": 'You have no balance to withdraw.'},
    'ar': {"wdPending": 'طلب سحب قيد المراجعة: {r} TRX', "wdInfo": 'يتم سحب كامل رصيدك مهما كان مقداره.', "c_min_balance": 'ليس لديك رصيد للسحب.'},
    'es': {"wdPending": 'Solicitud de retiro en revisión: {r} TRX', "wdInfo": 'Se retira todo tu saldo, sea cual sea el importe.', "c_min_balance": 'No tienes saldo para retirar.'},
    'de': {"wdPending": 'Auszahlungsantrag in Prüfung: {r} TRX', "wdInfo": 'Dein gesamtes Guthaben wird ausgezahlt, egal wie hoch.', "c_min_balance": 'Du hast kein Guthaben zum Auszahlen.'},
    'fr': {"wdPending": "Demande de retrait en cours d'examen : {r} TRX", "wdInfo": 'Tout votre solde est retiré, quel que soit le montant.', "c_min_balance": "Vous n'avez aucun solde à retirer."},
    'ru': {"wdPending": 'Заявка на вывод на проверке: {r} TRX', "wdInfo": 'Выводится весь баланс, независимо от суммы.', "c_min_balance": 'У вас нет средств для вывода.'},
    'pt': {"wdPending": 'Pedido de saque em análise: {r} TRX', "wdInfo": 'Todo o seu saldo é sacado, qualquer que seja o valor.', "c_min_balance": 'Você não tem saldo para sacar.'},
    'nl': {"wdPending": 'Opnameverzoek in beoordeling: {r} TRX', "wdInfo": 'Je hele saldo wordt opgenomen, ongeacht het bedrag.', "c_min_balance": 'Je hebt geen saldo om op te nemen.'},
    'pl': {"wdPending": 'Wniosek o wypłatę w trakcie weryfikacji: {r} TRX', "wdInfo": 'Wypłacane jest całe saldo, niezależnie od kwoty.', "c_min_balance": 'Nie masz salda do wypłaty.'},
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
            .replace("__AD_SDK__", "".join(
                ('<script src="%s"></script>' % html.escape(OC_SDK_URL, quote=True)) if n == "oc" else
                ('<script src="%s" data-zone="%s" data-sdk="show_%s"></script>' % (html.escape(MONETAG_SDK_URL, quote=True), MONETAG_ZONE, MONETAG_ZONE))
                for n in AD_NETS) if ADS_ENABLED else ""))
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

def wd_deadline(created):
    """نص الموعد النهائي لتحويل السحب والوقت المتبقي (48 ساعة افتراضياً)."""
    end = created + WITHDRAW_HOURS * 3600
    left = end - int(time.time())
    when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(end + ADMIN_TZ * 3600))
    if left <= 0:
        return "⏰ انتهت المهلة! (كان الموعد %s)" % when
    return "⏳ المهلة: %d ساعة و%d دقيقة\n📅 آخر موعد للتحويل: %s" % (left // 3600, left % 3600 // 60, when)

@bot.message_handler(commands=["myid"])
def cmd_myid(m):
    bot.reply_to(m, "آيديك: %d" % m.from_user.id)

@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        bot.reply_to(m, "هذا الأمر للأدمن فقط. آيديك: %d\nضع هذا الرقم في ADMIN_ID على Render." % m.from_user.id)
        return
    with tx() as c:
        rows = c.execute("SELECT w.*, u.username AS uname FROM withdrawals w LEFT JOIN users u ON u.user_id=w.user_id WHERE w.status='pending' ORDER BY w.id LIMIT 20").fetchall()
    if not rows:
        bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅")
        return
    for r in rows:
        bot.send_message(m.chat.id, "💸 طلب سحب #%d\n👤 %s | 🆔 %d\n💰 %.4f TRX\n📮 عنوان TRX:\n<code>%s</code>\n\n%s\n\n/paid %d  أو  /reject %d" % (
            r["id"], ("@" + html.escape(r["uname"])) if r["uname"] else "-", r["user_id"], r["amount"] / MICRO,
            html.escape(r["address"]), wd_deadline(r["created_at"]), r["id"], r["id"]), parse_mode="HTML", reply_markup=wd_buttons(r["id"]))

def wd_buttons(wid):
    """أزرار تحت رسالة السحب: تم الدفع / إلغاء الطلب."""
    mk = telebot.types.InlineKeyboardMarkup()
    mk.add(telebot.types.InlineKeyboardButton("✅ تم الدفع", callback_data="wd:p:%d" % wid),
           telebot.types.InlineKeyboardButton("❌ إلغاء الطلب", callback_data="wd:r:%d" % wid))
    return mk

def process_withdrawal(wid, paid, note=""):
    """ينفّذ الدفع أو الرفض (مع إرجاع الرصيد) ويُعلم المستخدم. يرجع None إن لم يوجد الطلب."""
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            return None
        lang = user_lang(c, w["user_id"])
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?", ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid:
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    try:
        if paid:
            bot.send_message(w["user_id"], msg_for(lang, "paid", amt=(f"{w['amount'] / MICRO:.4f}".rstrip("0").rstrip(".")), note=note))
        else:
            bot.send_message(w["user_id"], msg_for(lang, "rejected", id=wid, note=note))
    except Exception:
        pass
    return w

@bot.message_handler(commands=["paid", "reject"])
def cmd_process(m):
    if not is_admin(m):
        return
    args = (m.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(m, "الاستخدام: /paid 12 [رقم العملية]  أو  /reject 12")
        return
    wid, paid = int(args[1]), args[0].startswith("/paid")
    w = process_withdrawal(wid, paid, " ".join(args[2:]))
    if not w:
        bot.reply_to(m, "الطلب غير موجود أو تمت معالجته.")
        return
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")

@bot.callback_query_handler(func=lambda call: (call.data or "").startswith("wd:"))
def cb_withdrawal(call):
    if not (ADMIN_ID and call.from_user.id == ADMIN_ID):
        bot.answer_callback_query(call.id, "للأدمن فقط")
        return
    try:
        _, kind, wid = call.data.split(":")
        wid, paid = int(wid), kind == "p"
    except Exception:
        bot.answer_callback_query(call.id, "خطأ")
        return
    w = process_withdrawal(wid, paid)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    if not w:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تمت معالجته")
        return
    bot.answer_callback_query(call.id, "تم الدفع ✅" if paid else "تم الإلغاء وإرجاع الرصيد ❌")
    bot.send_message(call.message.chat.id, ("✅ تم الدفع للطلب #%d (%.4f TRX) وتم إشعار المستخدم." if paid else "❌ تم إلغاء الطلب #%d وأُرجع %.4f TRX لرصيد المستخدم.") % (wid, w["amount"] / MICRO))

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
