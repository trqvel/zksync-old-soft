from zksync_sdk import ZkSyncProviderV01, HttpJsonRPCTransport, network, ZkSync, EthereumProvider, Wallet, \
 ZkSyncSigner, EthereumSignerWeb3, ZkSyncLibrary
from zksync_sdk.types import ChangePubKeyEcdsa, RatioType
from string import digits, printable
from web3 import Web3, AsyncHTTPProvider, Account
import requests, json, time, asyncio, hmac, base64
from openpyxl import Workbook, load_workbook
from inspect import getsourcefile
from openpyxl.styles import Font
from fractions import Fraction
from datetime import datetime
from web3.eth import AsyncEth
from base58 import b58decode
from os.path import abspath
from decimal import Decimal
from codecs import encode
from loguru import logger
from eth_abi import abi
from tqdm import tqdm
import telebot
import random
import ctypes
import math
import sys
import os

sys.__stdout__ = sys.stdout # error with `import inquirer` without this string in some system
from inquirer import prompt, List

from abi import *
from setting import *


windll = ctypes.windll if os.name == 'nt' else None
PATH = '| *'+abspath(getsourcefile(lambda:0)).split("\\")[-2]+'*'
list_send = []
outfile = ''

with open(f"{outfile}wallets.txt", "r") as f:
    WALLETS = [row.strip() for row in f]

with open(f"{outfile}recipients.txt", "r") as f:
    RECIPIENTS = [row.strip() for row in f]

with open(f"{outfile}proxies.txt", "r") as f:
    PROXIES = [row.strip() for row in f]

ORBITER_MAKER = json.loads(ORBITER_MAKER_)

os.environ["ZK_SYNC_LIBRARY_PATH"] = ZK_SYNC_LIBRARY_PATH

def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(qty, decimal):
    return qty/ int("".join((["1"]+ ["0"]*decimal)))

def call_json(result, outfile):
    with open(f"{outfile}.json", "w") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

def sleeping(*timing):
    if len(timing) == 2: x = random.randint(timing[0], timing[1])
    else: x = timing[0]
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        time.sleep(1)


def get_native_prices():

    try:

        url = f'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT'

        response = requests.get(url)

        if response.status_code == 200:
            result  = [response.json()]
            price   = result[0]['price']
            return float(price) # ETH price
        else:
            logger.error(f'response.status_code : {response.status_code}. try again')
            time.sleep(5)
            return get_native_prices()

    except Exception as error:
        logger.error(f'get_native_prices error : {error}. try again')
        time.sleep(5)
        return get_native_prices()

def send_msg(text=False, sticker=False):
        if not text: str_send = '\n'.join(list_send)
        else: str_send = text
        bot = telebot.TeleBot(TG_TOKEN, disable_web_page_preview=True, parse_mode='HTML')
        sticker_ = random.choice(STICKERS_PACK)
        for tg_id in TG_IDS:
            try:
                if sticker:
                        bot.send_sticker(tg_id, sticker_)
                else:
                    bot.send_message(tg_id, str_send)
            except Exception as error:
                logger.error(f'tg send error: {error}')


def change_proxy():
    counter = 0
    while True:
        try:
            r = requests.get(PROXY_CHANGE_LINK)
            if r.json().get('status') == 'OK':
                return r.json()['new_ip']
            else: raise ValueError(r.json())

        except Exception as err:
            if 'Already change IP, please wait' in str(err):
                logger.warning('Already change IP, please wait')
                time.sleep(10)
            elif counter < RETRY:
                counter += 1
                logger.error(f'Cant change proxy: {err}')
                logger.error(f'text: {r.text}')
                time.sleep(10)
            else:
                counter = 0
                send_msg('🚧 не могу поменять айпи прокси 🚧')
                input('\nPress Enter to continue...\n> Enter')

STR_DONE    = '✅ '
STR_CANCEL  = '❌ '

WALLETS_PROXIES = {}
ETH_PRICE       = get_native_prices()
if len(WALLETS) != len(RECIPIENTS): raise ValueError(f'Wallets amount must be = recipients amount! ({len(WALLETS)}≠{len(RECIPIENTS)})')
RECIPIENTS_WALLETS  = dict(zip(WALLETS, RECIPIENTS))

# на сколько делить газ лимит
DIVIDERS = {
    'mintsquare'    : 1,
    '1inch'         : 1,
    'syncswap_swap' : 1,
    'syncswap_pool' : 1,
    'approve'       : 1,
    'orbiter'       : 1,
    'bungee'        : 1,
    'transfer'      : 1,
    'mute_swap'     : 1,
    'space_swap'    : 1,
    'bridge_to_eth' : 1,
}

CHAINS_ID = {
    'ethereum'      : 101,
    'bsc'           : 102,
    'avalanche'     : 106,
    'aptos'         : 108,
    'polygon'       : 109,
    'arbitrum'      : 110,
    'optimism'      : 111,
    'fantom'        : 112,
    'harmony'       : 116,
    'goerli'        : 154,
    'polygon_zkevm' : 158,
    'zksync'        : 165,
    'tenet'         : 173,
    'nova'          : 175,
    'meter'         : 176,
}

ORBITER_AMOUNT = {
    'ethereum'      : 0.000000000000009001,
    'optimism'      : 0.000000000000009007,
    'bsc'           : 0.000000000000009015,
    'arbitrum'      : 0.000000000000009002,
    'nova'          : 0.000000000000009016,
    'polygon'       : 0.000000000000009006,
    'polygon_zkevm' : 0.000000000000009017,
    'zksync'        : 0.000000000000009014,
    'zksync_lite'   : 0.000000000000009003,
    'starknet'      : 0.000000000000009004,
}

ORBITER_AMOUNT_STR = {
    'ethereum'      : '9001',
    'optimism'      : '9007',
    'bsc'           : '9015',
    'arbitrum'      : '9002',
    'nova'          : '9016',
    'polygon'       : '9006',
    'polygon_zkevm' : '9017',
    'zksync'        : '9014',
    'zksync_lite'   : '9003',
    'starknet'      : '9004',
}

BUNGEE_CONTRACTS = {
    'ethereum'      : '0xb584D4bE1A5470CA1a8778E9B86c81e165204599',
    'optimism'      : '0x5800249621da520adfdca16da20d8a5fc0f814d8',
    'bsc'           : '0xbe51d38547992293c89cc589105784ab60b004a9',
    'arbitrum'      : '0xc0e02aa55d10e38855e13b64a8e1387a04681a00',
    'polygon'       : '0xAC313d7491910516E06FBfC2A0b5BB49bb072D91',
    'polygon_zkevm' : '0x555a64968e4803e27669d64e349ef3d18fca0895',
    'zksync'        : '0x7Ee459D7fDe8b4a3C22b9c8C7aa52AbadDd9fFD5',
    'avalanche'     : '0x040993fbf458b95871cd2d73ee2e09f4af6d56bb',
}

SYNCSWAP_POOLS =  {
    'usdc'  : "0x80115c708E12eDd42E504c1cD52Aea96C547c05c",
    'zat'   : "0x2A936038B695F48b68a560cf01C4Cf8899616C5c",
    'matic' : "0x49EFB4cE6d7e80B6fC5a06829e3de00344FFF65E",
    'busd'  : "0xaD86486f1d225D624443e5DF4B2301d03bBe70f6",
    'bnb'   : "0x8De3827E7Ba9cdD6BE9b88BA25F8A22dA0D7851d",
    'avax'  : "0x743954d87E81350E2f35D9D12A41dbA309ACbD2e",
    'wbtc'  : "0xb3479139e07568BA954C8a14D5a8B3466e35533d",
    'usdt'  : "0xd3D91634Cf4C04aD1B76cE2c06F7385A897F54D3",
    'pepe'  : "0x494d4EcFF27765f3485877DbAECA2AFd67D3318f",
    'lusd'  : "0x4E7d2e3f40998DaeB59a316148BFbF8efd1F7F3c"
}

MUTESWAP_POOLS =  {
    'usdc'  : "0xDFAaB828f5F515E104BaaBa4d8D554DA9096f0e4",
    'mute'  : "0xb85feb6aF3412d690DFDA280b73EaED73a2315bC",
}

SPACEFI_POOLS =  {
    'usdc'  : "0xD0cE094412898760C2A5e37AbeC39b0E785b45aE",
}

VELOCORE_POOLS =  {
    'usdc'  : "0xb3120ad6c3285fc4e422581d9ad003277802cc47",
}

ZKSYNC_TOKENS_CONTACT = {
    'eth'   : "0x5aea5775959fbc2557cc8789bc1bf90a239d9a91",
    'usdc'  : "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
    'space' : "0x47260090cE5e83454d5f05A0AbbB2C953835f777",
    'xspace': "0x6aF43486Cb84bE0e3EDdCef93d3C43Ef0C5F63b1",
    'zat'   : "0x47EF4A5641992A72CFd57b9406c9D9cefEE8e0C4",
    'matic' : "0x28a487240e4D45CfF4A2980D334CC933B7483842",
    'busd'  : "0x2039bb4116B4EFc145Ec4f0e2eA75012D6C0f181",
    'bnb'   : "0x7400793aAd94C8CA801aa036357d10F5Fd0ce08f",
    'avax'  : "0x6A5279E99CA7786fb13F827Fc1Fb4F61684933d6",
    'mute'  : "0x0e97c7a0f8b2c9885c8ac9fc6136e829cbc21d42",
    'wisp'  : "0xc8ec5b0627c794de0e4ea5d97ad9a556b361d243",
    'zkdoge': "0xbfb4b5616044eded03e5b1ad75141f0d9cb1499b",
    'zkpad' : "0x959ab3394246669914bddeaeb50f8ac85648615e",
    'wbtc'  : "0xb3479139e07568BA954C8a14D5a8B3466e35533d",
    'usdt'  : "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C",
    'pepe'  : "0xFD282F16a64c6D304aC05d1A58Da15bed0467c71",
    'lusd'  : "0x503234F203fC7Eb888EEC8513210612a43Cf6115"
}

INCH_SPENDERS = {
    'ethereum'      : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'optimism'      : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'bsc'           : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'polygon'       : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'polygon_zkevm' : 'NETY',
    'arbitrum'      : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'avalanche'     : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'fantom'        : '0x1111111254eeb25477b68fb85ed929f73a960582',
    'nova'          : 'NETY',
    'zksync'        : '0x6e2b76966cbd9cf4cc2fa0d76d24d5241e0abc2f',
    'zksync_lite'   : 'NETY'
}

STICKERS_PACK = [
            'CAACAgIAAxkBAAEJdPVklYrW475BYNg7-hGpf9D9DL6GHQAChxQAAmlPMEuEdoX6ZrLUMC8E',
            'CAACAgIAAxkBAAEJdQVklYty5HIQIBsth0bh5z6IE6RIBgACERoAAgyXMEv2ScmUbUXpGC8E',
            'CAACAgUAAxkBAAEJdQdklYvErT64GV9gOYQ3BHmd3WoVKwAC0wUAAu238FenBwABc6yB33QvBA',
            'CAACAgUAAxkBAAEJdRFklYviX-GcPIJdAllqK2gSr1YJTQACJQQAAkDM8FcxDG81jZ5xKS8E',
            'CAACAgQAAxkBAAEJdRNklYwOoRC79U1Vt94r3L8qQlMFqQAC-Q0AAse0kVMlfVlz7AesOi8E',
            'CAACAgQAAxkBAAEJdRVklYwQzBPx7rriKdRfl5M52M2nagACUwEAAqghIQZ1rkmKmtzlYS8E',
            'CAACAgQAAxkBAAEJdRtklYw6Q-5PxVc5rKz1WFSMVjd5NgACMAwAAktp7hA2Nlov_ow82S8E',
            'CAACAgIAAxkBAAEJdSVklYx3vQfY7Nt38SuD4bpQIjLn-wACIQsAAhXgCEgCX7OVbl2CWC8E'
]

NFT_COLLECTIONS = [
        {'cid': "QmdYeDpkVZedk1mkGodjNmF35UNxwafhFLVvsHrWgJoz6A/beanz_metadata", 'supply': 19000},    # azuki beanz
        {'cid': "QmZcH4YvBVVRJtdn4RdbaqgspFU8gH6P9vomDpBVpAL3u4", 'supply': 10000},                   # azuki
        {'cid': "QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq", 'supply': 10000},                   # BAYC
        {'cid': "QmaN1jRPtmzeqhp6s3mR1SRK4q1xWPvFvwqW1jyN6trir9", 'supply': 20000},                   # Nakamigos
        {'cid': "QmSARWPw2tAoVwZMqBLjxSh2qKCZ8qBimxZccTkWnNBggh", 'supply': 17000},                   # PixelBubbies
        {'cid': "QmPMc4tcBsMqLRuCQtPmPe84bpSjrC3Ky7t3JWuHXYB4aS", 'supply': 10000},                   # Doodles
        {'cid': "QmU7pgaLsVkrP1ao7pn51wDE37PYNime6pV6mx8sUx1Nr4", 'supply': 10000},                   # ForgottenRunesWizardsCult
        {'cid': "QmWiQE65tmpYzcokCheQmng2DCM33DEhjXcPB6PanwpAZo", 'supply': 10000},                   # mfer
        {'cid': "QmUEiYGcZJWZWp9LNCTL5PGhGcjGvokKfcaCoj23dbp79J", 'supply': 10000},                   # SHIBOSHIS
        {'cid': "QmXUUXRSAJeb4u8p4yKHmXN1iAKtAV7jwLHjw35TNm5jN7", 'supply': 10000},                   # Sappy Seals
    ]

text = r"""
   ▒▄███▀██▀ ██ ▄█▀  ██████▓██   ██▓ ███▄    █  ▄████▄     ▓█████  ▄▄▄▄    ▄▄▄     ▓███████▓▓█████  ██▓  ██▒   
     ░ ░▄█▀░  ██▄█▒ ▒██    ▒ ▒██  ██▒ ██ ▀█   █ ▒██▀ ▀█     ▓█   ▀ ▓█████▄ ▒████▄   ▓  ██▒ ▓▒▓█   ▀ ▓██▒  ░█▒░  
    ░░▄█▀▀▒░ ▓███▄░ ░ ▓██▄    ▒██ ██░▓██  ▀█ ██▒▒▓█    ▄    ▒███   ▒██▒ ▄██▒██  ▀█▄ ▒ ▓██░ ▒░▒███   ▒██░   ▒▒ 
   ░▄█▀▒ ░ ░▓██ █▄   ▒   ██▒ ░ ▐██▓░▓██▒  ▐▌██▒▒▓▓▄ ▄██▒   ▒▓█  ▄ ▒██░█▀  ░██▄▄▄▄██░ ▓██▓ ░ ▒▓█  ▄ ▒██░    ░
    ███████▒▒██▒ █▄▒██████▒▒ ░ ██▒▓░▒██░   ▓██░▒ ▓███▀ ░   ░▒████▒░▓█  ▀█▓ ▓█   ▓██▒ ▒██▒ ░ ░▒████▒░██████▒░
    ▒▒ ▓░▒░▒▒ ▒▒ ▓▒▒ ▒▓▒ ▒ ░  ██▒▒▒ ░ ▒░   ▒ ▒ ░ ░▒ ▒  ░   ░░ ▒░ ░░▒▓███▀▒ ▒▒   ▓▒█░ ▒ ░░   ░░ ▒░ ░░ ▒░▓  ░
   ░░▒ ▒ ░ ▒░ ░▒ ▒░░ ░▒  ░ ░▓██ ░▒░ ░ ░░   ░ ▒░  ░  ▒       ░ ░  ░▒░▒   ░   ▒   ▒▒ ░   ░     ░ ░  ░░ ░ ▒  ░
   ░ ░ ░ ░ ░░ ░░ ░ ░  ░  ░  ▒ ▒ ░░     ░   ░ ░ ░              ░    ░    ░   ░   ▒    ░         ░     ░ ░   
     ░ ░    ░  ░         ░  ░ ░              ░ ░ ░            ░  ░ ░            ░  ░           ░  ░    ░  ░
   ░                        ░ ░                ░                        ░                                                                                                                                                                                                                                                                           
"""
logger.remove()
logger.add(sys.stderr, format="<level>{message}</level>")
logger.error(text)
logger.remove()
logger.add(sys.stderr, format="<white>{time:HH:mm:ss:SSS}</white> | <level>{level: <8}</level> | <level>{message}</level>")

