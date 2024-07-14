
#################### PROXY ####################
USE_PROXY   = False # True / False
# если USE_PROXY = True и юзаешь мобильные - настрой следующие два пункта, если обычные прокси - оставь пустым и заполни proxies.txt.
# ТОЛЬКО ДЛЯ МОБИЛЬНЫХ ПРОКСИ:
PROXY_CHANGE_LINK = '' # https://mobileproxy.space/reload.html?proxy_key=........&format=json
PROXY_DATA = '' # http://LOGIN:PASSWORD@IP:PORT


CHECK_GWEI  = True # True / False
MAX_GWEI    = 20 # если gas в gwei выше этого числа, скрипт будет висеть в ожидании (смотреть здесь : https://etherscan.io/gastracker)

RANDOM_WALLETS  = True # True / False | нужно ли рандомизировать (перемешивать) кошельки

RETRY = 5 # кол-во попыток при ошибках / фейлах

TG_BOT_SEND = True # True / False. нужно ли отправлять результаты в тг бота
TG_TOKEN = '123:AA'
TG_IDS = [
    ,
    # 1684654564,
    # 4556456,
]

ZK_SYNC_LIBRARY_PATH = r'...\zksync_sdk\zks-crypto-x86_64-pc-windows-gnu.dll' # путь к скачанному .dll файлу zksync

DATA = {
    'ethereum'      : {'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx', 'token': 'ETH', 'chain_id': 1},
    'zksync'        : {'rpc': 'https://rpc.ankr.com/zksync_era', 'scan': 'https://explorer.zksync.io/tx', 'token': 'ETH', 'chain_id': 324},
    'zksync_lite'   : {'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://zkscan.io/explorer/transactions', 'token': 'ETH', 'chain_id': ''},
    'arbitrum'      : {'rpc': 'https://rpc.ankr.com/arbitrum', 'scan': 'https://arbiscan.io/tx', 'token': 'ETH', 'chain_id': 42161},
}

OKX_KEYS = {
    'account_1' : {
        'api_key': '',
        'api_secret': '',
        'password': '',
    },
    'account_2' : {
        'api_key'   : '',
        'api_secret': '',
        'password'  : '',
    },
}


TRANSACTIONS_COUNT = {
    'syncswap_swap'          : [1,2], # do module 1-3 time randomly
    'mute_swap'              : [1,2],
    'space_swap'             : [1,2],
    'bridge_to_eth_from_era' : [1,2],
    'merkly'                 : [0,1],
    'velocore_swap'          : [1,2],
    'izumi_swap'             : [1,2],
    'odos'                   : [1,3], # eth -> stable + ([1,3] * stable -> stable) + stable -> eth
    'eralend'                : [1,3],
    'dmail'                  : [8,15],
    'zk_lite_mint_nft'       : [0,2],
}

# если газ за транзу с этой сети будет выше в $, тогда скрипт будет спать
MAX_GAS = {
    'avalanche'     : 1,
    'polygon'       : 1,
    'ethereum'      : 4.6,
    'bsc'           : 0.7,
    'arbitrum'      : 1,
    'optimism'      : 1,
    'fantom'        : 1,
    'zksync'        : 2.6,
}

def value_okx():

    symbol      = 'ETH'

    amount_from = 0.09
    amount_to   = 0.095

    account = 'account_1' # аккаунт okx берется из data/data.py

    SUB_ACC = True

    return symbol, amount_from, amount_to, account, SUB_ACC

def value_zksync_bridge():
    '''
    бридж из эфира в эру через офф мост https://bridge.zksync.io/
    будет бриджить весь балик, оставляя только значение keep
    '''

    keep_from = 0.001 # balance - keep
    keep_to = 0.0015

    return keep_from, keep_to

def value_syncswap():
    '''
    если make_pool = True, тогда будет кидать в пул
    '''

    tokens = [
        'usdc',
        # 'zat',
        # 'matic',
        # 'busd',
        # 'bnb',
        # 'avax'
        ]

    amount_from = 0.000001 # от скольки эфира свапать в токен
    amount_to   = 0.000005 # до скольки эфира свапать в токен

    amount_token_from = 0.75    # свапнуть от 75% из токена обратно в эфир
    amount_token_to   = 0.95    # свапнуть до 95% из токена обратно в эфир

    make_pool   = True # True / False

    eth_to_pool_from = 0.000001 # от скольки эфира кидать в пул (если make_pool = True)
    eth_to_pool_to   = 0.00001  # до скольки эфира кидать в пул

    token_to_pool_from  = 0.001 # закинуть в пул от 0.1% баланса токена
    token_to_pool_to    = 0.01  # закинуть в пул до 1% баланса токена

    return amount_from, amount_to, amount_token_from, amount_token_to, eth_to_pool_from, eth_to_pool_to, token_to_pool_from, token_to_pool_to, tokens, make_pool

def value_muteswap():

    tokens = [
        'usdc',
        'mute',
        # 'wisp',
        # 'zkdoge',
        # 'zkpad',
        ]

    amount_from = 0.0000057 # 0.01$
    amount_to   = 0.00011   # 0.20$

    amount_token_from = 0.75    # свапнуть от 75% из токена обратно в эфир
    amount_token_to   = 0.95    # свапнуть до 95% из токена обратно в эфир

    slippage = 1 # = 1% | при 0.5% фейлит

    make_pool = True # в ликвидность зальется 1% от баланса токена

    token_to_pool_from  = 0.001 # закинуть в пул от 0.1% баланса токена
    token_to_pool_to    = 0.01  # закинуть в пул до 1% баланса токена

    return amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool

def value_velocore():

    tokens = [
        'usdc',
        # 'busd', # для него нету пула ликвидности. можно раскомментить если make_pool = False
        ]

    amount_from = 0.0000057 # 0.01$
    amount_to   = 0.00011   # 0.20$

    amount_token_from = 0.985   # свапнуть от 98.5% из токена обратно в эфир
    amount_token_to   = 1       # свапнуть до 100% из токена обратно в эфир

    slippage = 1 # = 1%

    make_pool = True
    token_to_pool_from  = 0.001 # закинуть в пул от 0.1% баланса токена и эквивалентное количество эфира
    token_to_pool_to    = 0.01  # закинуть в пул до 1% баланса токена и эквивалентное количество эфира

    return amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool

def value_izumi():

    tokens = [
        'usdc',
        # в пулах с остальными токенами ликвидность меньше 10к
        ]

    amount_from = 0.0000057 # 0.01$
    amount_to   = 0.00015   # 0.20$

    amount_token_from = 0.985   # свапнуть от 98.5% из токена обратно в эфир
    amount_token_to   = 1       # свапнуть до 100% из токена обратно в эфир

    slippage = 0.3 # = 0.3%

    return amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage

def value_spaceswap():

    tokens = [
        'usdc',
        'space', # если будет выбран этот токен то после обратной конвертации будет получено 0.5х. подробнее в value_space_convert()
        ]

    amount_from = 0.0000057 # 0.01$
    amount_to   = 0.00011   # 0.20$

    amount_token_from = 0.75    # свапнуть от 75% из токена обратно в эфир
    amount_token_to   = 0.95    # свапнуть до 95% из токена обратно в эфир

    slippage = 0.5 # = 0.5%

    make_pool = True  # True / False

    token_to_pool_from  = 0.001 # закинуть в пул от 0.1% баланса токена
    token_to_pool_to    = 0.01  # закинуть в пул до 1% баланса токена

    return amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool

def value_space_convert():
    """
    https://app.spacefi.io/#/xSPACE
    настройка конкретно для токена SPACE:
    convert SPACE -> xSPACE -> SPACE
    после анстейка будет получено в 2 раза меньше space, чем было застейкано
    """

    amount_from = 30 # stake from 30% of token balance
    amount_to   = 80 # stake to 80% of token balance

    return amount_from, amount_to

def value_era_to_eth():
    """
    https://bridge.zksync.io/withdraw
    бридж эфира из Era в Ethereum
    """

    amount_from = 0.00003 # ETH  ~0.05$
    amount_to   = 0.0003  # ETH  ~0.5$

    return amount_from, amount_to

def value_merkly():
    """
    минт нфт и бридж в рандомную сеть из указанных через https://minter.merkly.com/
    """
    chains = (
        'avalanche',        # ~0.51$
        'meter',            # ~0.14$
        'tenet',            # ~0.02$
        'optimism',         # ~0.71$
        'nova',             # ~0.02$
        'polygon_zkevm',    # ~0.78$
        'bsc',              # ~0.72$
    )

    return chains

def value_odos():
    """
    https://app.odos.xyz/
    свапы USDC/USDT/BUSD
    на последнем свапе Stable-ETH и свапах между двумя стейблами - свапается весь баланс
    """

    swap_from = 0.85 # на первом свапе - свапать от 85% баланса из ETH в стейбл
    swap_to   = 0.9 # на первом свапе - свапать до 90% баланса из ETH в стейбл

    max_difference = 1.2 # максимальная разница при свапе между двумя стейблами. например при свапе 1000$ минимально должны получить 1000-1.2 = 998.8$. иначе пробуем свапнуть в другой токен

    return swap_from, swap_to, max_difference

def value_orbiter():
    '''
    бридж нативных токенов через https://www.orbiter.finance/
    из ZkEra в ZkLite - будет бриджить в указанном диапазоне transfer_from - transfer_to
    '''

    keep_values = {
        'zksync_lite': {    # for ZkSync Era -> ZkSync Lite
            'transfer_from': 0.002,
            'transfer_to': 0.0025,
        }
    }

    return keep_values

def value_keep_transfer():
    '''
    будет отправлять весь балик на OKX в Arbitrum, оставляя только значение keep
    '''

    keep_from = 0.00015
    keep_to = 0.0005

    return keep_from, keep_to


def value_across():
    '''
    бридж нативных токенов через https://across.to/bridge | так же работает и для orbiter Era -> Arbitrum
    будет бриджить весь балик, оставляя только значение keep_from - keep_to
    '''

    keep_from   = 0.0085
    keep_to     = 0.0105

    return keep_from, keep_to


def value_eralend():
    '''

    '''

    min_amount_eth = 0 # сколько эфира закидывать в пул. если нужно юзать в процентах - оставляй 0 и заполняй percent_eth
    max_amount_eth = 0
    min_percent_eth = 60 # сколько процентов от баланса закинуть в пул. работает только в случае если пред. 2 параметра = 0.
    max_percent_eth = 80

    min_borrow = 60 # %
    max_borrow = 80 # % | do not increase it

    return min_amount_eth, max_amount_eth, min_percent_eth, max_percent_eth, min_borrow, max_borrow

