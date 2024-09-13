from config import *
from hashlib import sha256
from setting import USE_PROXY, PROXY_DATA

# ============ web3_helpers ============

def evm_wallet(key):

    try:
        chain = 'ethereum'
        web3 = get_web3(chain, key)
        wallet = web3.eth.account.from_key(key).address
        return wallet
    except:
        return key

def wait_balance(privatekey, chain, min_balance, token=False):
    logger.debug(f'wait {round(Decimal(min_balance), 8)} in {chain}')

    while True:
        try:
            if not token:
                humanReadable = check_balance(privatekey, chain)
            else:
                humanReadable = check_balance(privatekey, chain, token)

            if humanReadable >= min_balance:
                logger.info(f'balance : {humanReadable}')
                break
            time.sleep(15)
        except Exception as error:
            logger.error(f'wait balance error: {error}, sleeping 60 secs...')
            time.sleep(60)

def sign_tx(web3, contract_txn, privatekey):
    signed_tx = web3.eth.account.sign_transaction(contract_txn, privatekey)
    raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash = web3.to_hex(raw_tx_hash)
    
    return tx_hash

def check_data_token(web3, token_address):
    while True:
        try:
            token_contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            decimals        = token_contract.functions.decimals().call()
            symbol          = token_contract.functions.symbol().call()

            return token_contract, decimals, symbol

        except Exception as error:
            logger.error(f'check token data error: {error}')
            time.sleep(10)

def check_status_tx(chain, tx_hash, text='checking tx_status'):

    logger.info(f'{chain} {text} : {tx_hash}')

    while True:
        try:
            web3        = get_web3(chain)
            status_     = web3.eth.get_transaction_receipt(tx_hash)
            status      = status_["status"]
            if status in [0, 1]:
                return status
            time.sleep(1)
        except Exception as error:
            # logger.info(f'error, try again : {error}')
            time.sleep(1)

def add_gas_limit(web3, contract_txn, change_value=True):
    value = contract_txn['value']
    if change_value:
        contract_txn['value'] = 0
    pluser = [1.02, 1.05]
    gasLimit = web3.eth.estimate_gas(contract_txn)
    contract_txn['gas'] = int(gasLimit * random.uniform(pluser[0], pluser[1]))

    contract_txn['value'] = value
    return contract_txn

def add_gas_price(web3, contract_txn):

    try:
        gas_price = web3.eth.gas_price
        contract_txn['gasPrice'] = int(gas_price * random.uniform(1.02, 1.05))
    except Exception as error: 
        logger.error(error)

    return contract_txn

def round_to(num, digits=3):
    try:
        if num == 0: return 0
        scale = int(-math.floor(math.log10(abs(num - int(num))))) + digits - 1
        if scale < digits: scale = digits
        return round(num, scale)
    except: return num

def check_balance(privatekey, chain, address_contract=False, human=True):
    try:

        web3 = get_web3(chain, privatekey)

        try     : wallet = web3.eth.account.from_key(privatekey).address
        except  : wallet = privatekey
            
        if address_contract in ['', False]: # eth
            balance         = web3.eth.get_balance(web3.to_checksum_address(wallet))
            token_decimal   = 18
        else:
            token_contract, token_decimal, symbol = check_data_token(web3, address_contract)
            balance = token_contract.functions.balanceOf(web3.to_checksum_address(wallet)).call()

        if not human:
            return balance

        human_readable = decimalToInt(balance, token_decimal) 

        return human_readable

    except Exception as error:
        logger.error(error)
        time.sleep(5)
        check_balance(privatekey, chain, address_contract, human)

def check_allowance(chain, token_address, privatekey, spender):

    try:
        web3 = get_web3(chain, privatekey)
        wallet = web3.eth.account.from_key(privatekey).address
        contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        amount_approved = contract.functions.allowance(wallet, spender).call()
        return amount_approved
    except Exception as error:
        logger.error(error)

def checker_total_fee(chain, gas):

    gas = decimalToInt(gas, 18) * ETH_PRICE

    if gas > MAX_GAS[chain]:
        logger.info(f'gas is too high : {round_to(gas)} $ > {MAX_GAS[chain]} $. sleep and try check again')
        sleeping(30)
        return False
    else:
        return True

def get_base_gas():

    try:
        web3 = get_web3('ethereum')
        gas_price = web3.eth.gas_price
        gwei_gas_price = web3.from_wei(gas_price, 'gwei')

        return gwei_gas_price
    
    except Exception as error: 
        logger.error(f'get base gas err: {error}')
        return get_base_gas()

def wait_gas(first=True):
    while True:
        current_gas = get_base_gas()

        if current_gas > MAX_GWEI:
            if first:
                logger.info(f'current_gas : {current_gas} > {MAX_GWEI}')
                first = False
            time.sleep(10)
        else: return current_gas

def get_web3(chain, wallet=False):

    rpc = DATA[chain]['rpc']

    proxy_data = get_proxy()

    if proxy_data != False:
        while True:
            try:
                # proxy = WALLETS_PROXIES[wallet]
                proxy = proxy_data['proxy']
                web3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"proxies":{'https' : proxy, 'http' : proxy}}))
                break
            except Exception as error:
                logger.error(f'{error}. Cant connect to proxy ({proxy})')
                send_msg('🚧 не могу подключить прокси к web3 🚧')
                input('\nPress Enter to continue...\n> Enter')


    else:
        web3 = Web3(Web3.HTTPProvider(rpc))

    return web3


# ============== help modules ==============

def update_name(account_num=0, modules_counter=0, modules=0, on_return=False, on_welcome=False):
    version = '1.2'

    if on_welcome:
        if os.name == 'nt':
            windll.kernel32.SetConsoleTitleW(f'ZkSync v{version} {PATH}')
        return
    total_len = 0
    modules_names = []
    for module in modules:
        if type(module) == list:
            total_len += len(module)
            ([modules_names.append(mod.__name__) for mod in module])
        elif callable(module): # if type == function
            total_len += 1
            modules_names.append(module.__name__)
        elif type(module) == int:
            total_len += module
        else:
            logger.warning(f'no condition with type "{type(module)}" ({module})')

    if on_return:
        return f'account [{account_num}/{len(WALLETS)}] | modules [{modules_counter}/{total_len}] {PATH}'
    if os.name == 'nt':
        windll.kernel32.SetConsoleTitleW(f'ZkSync v{version} '
                                         f'| account [{account_num}/{len(WALLETS)}] '
                                         f'| modules [{modules_counter}/{total_len}]'
                                         f' {PATH}')

def pick_path():
    questions = [
        List('prefered_path', message="What path do you prefer?",
             choices=[
                'Path 1 | Only do Era+Lite modules',
                'Path 2 | Only take tokens from pools',
                'Path 3 | Do only Era modules + Take tokens from pools',
                'Path 4 | OKX -> Ethereum -> Era -> All Modules + Odos -> ZkLite -> Arbitrum -> OKX',
                'Path 5 | OKX -> Era -> All Modules + Odos -> ZkLite -> Arbitrum -> OKX',
                'Path 6 | OKX -> Era -> All Era+Lite Modules + Odos -> Arbitrum -> OKX',
                'Path 7 | OKX -> Era -> All Era+Lite Modules + Eralend -> Arbitrum -> OKX'
             ]
        )
    ]
    path = prompt(questions)['prefered_path']
    if 'Path 1 |' in path:
        PATH = '1'
    elif 'Path 2 |' in path:
        PATH = '2'
    elif 'Path 3 |' in path:
        PATH = '3'
    elif 'Path 4 |' in path:
        PATH = '4'
    elif 'Path 5 |' in path:
        PATH = '5'
    elif 'Path 6 |' in path:
        PATH = '6'
    elif 'Path 7 |' in path:
        PATH = '7'

    return PATH

def create_excel(wallets):
    web3 = get_web3("ethereum")
    workbook = Workbook()
    sheet = workbook.active

    sheet['A1'] = 'Privatekey'
    sheet['B1'] = 'Address'
    sheet['C1'] = 'Date'
    sheet['A1'].font = Font(bold=True)
    sheet['B1'].font = Font(bold=True)
    sheet['C1'].font = Font(bold=True)

    for index in range(len(wallets)):
        sheet[f'A{index+2}'] = wallets[index]
        sheet[f'B{index+2}'] = web3.eth.account.from_key(wallets[index]).address

    file_name = f'{len(wallets)}wallets_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    workbook.save(file_name)
    return file_name

def replace_excel(file_name, needed_address):
    workbook = load_workbook(file_name)
    sheet = workbook.active

    for row in sheet.iter_rows(min_row=2):
        if row[0].value == needed_address:
            row[2].value = datetime.now().strftime("%d.%m.%Y %H:%M")
    try:
        workbook.save(file_name)
    except PermissionError:
        logger.error(f'cant save excel file, close it! | {needed_address} - {datetime.now().strftime("%d.%m.%Y %H:%M")}')

def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=USDT", body='', meth="GET"):

    try:
        import datetime
        def signature(
            timestamp: str, method: str, request_path: str, secret_key: str, body: str = ""
        ) -> str:
            if not body:
                body = ""

            message = timestamp + method.upper() + request_path + body
            mac = hmac.new(
                bytes(secret_key, encoding="utf-8"),
                bytes(message, encoding="utf-8"),
                digestmod="sha256",
            )
            d = mac.digest()
            return base64.b64encode(d).decode("utf-8")

        dt_now = datetime.datetime.utcnow()
        ms = str(dt_now.microsecond).zfill(6)[:3]
        timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

        base_url = "https://www.okex.com"
        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": signature(timestamp, meth, request_path, secret_key, body),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphras,
            'x-simulated-trading': '0'
        }
    except Exception as ex:
        logger.error(ex)
    return base_url, request_path, headers

def check_orbiter_limits(from_chain, to_chain):
    orbiter_ids = {
        'ethereum': '1',
        'optimism': '7',
        'bsc': '15',
        'arbitrum': '2',
        'nova': '16',
        'polygon': '6',
        'polygon_zkevm': '17',
        'zksync': '14',
        'zksync_lite': '3',
        'starknet': '4',
    }

    from_maker = orbiter_ids[from_chain]
    to_maker = orbiter_ids[to_chain]

    maker_x_maker = f'{from_maker}-{to_maker}'

    for maker in ORBITER_MAKER:

        if maker_x_maker == maker:
            min_bridge = ORBITER_MAKER[maker]['ETH-ETH']['minPrice']
            max_bridge = ORBITER_MAKER[maker]['ETH-ETH']['maxPrice']
            fees = ORBITER_MAKER[maker]['ETH-ETH']['tradingFee']

            return min_bridge, max_bridge, fees

def get_orbiter_value(base_num, chain, from_chain):
    base_num_dec = Decimal(str(base_num))
    orbiter_amount_dec = Decimal(str(ORBITER_AMOUNT[chain]))
    if from_chain == 'zksync_lite': orbiter_amount_dec = orbiter_amount_dec * 10 ** 6
    difference = base_num_dec - orbiter_amount_dec
    random_offset = Decimal(str(random.uniform(-0.000000000000001, 0.000000000000001)))
    result_dec = difference + random_offset
    orbiter_str = ORBITER_AMOUNT_STR[chain][-4:]
    result_str_ = '{:.18f}'.format(result_dec.quantize(Decimal('0.000000000000000001')))
    if from_chain == 'zksync_lite': result_str_ = '{:.12f}'.format(result_dec.quantize(Decimal('0.000000000001')))
    result_str = result_str_[:-4] + orbiter_str

    return Decimal(result_str)

def mintsquare_random_tokenURI(retry=0):
    try:

        module_str = f'get_random_tokenURI_MintSquare'

        URL = "https://api.mintsquare.io/nft/metadata/zksync-mainnet/0x53ec17bd635f7a54b3551e76fd53db8881028fc3/" + str(
            random.randint(40000, 450000))

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }

        # запрос может быть заблокирован CloudFlare. Вроде этих хедеров хватает, чтобы не блокировало
        r = requests.get(url=URL, timeout=5, headers=headers)

        if r.status_code == 200:
            tokenURI = r.json()["TokenURI"]
            return tokenURI

        else:
            logger.error(f'{module_str} | blocked by CloudFlare. Try again')
            time.sleep(10)
            if retry < RETRY:
                return mintsquare_random_tokenURI(retry + 1)


    except Exception as error:
        logger.error(f'{error}. Try again')
        time.sleep(10)
        if retry < RETRY:
            return mintsquare_random_tokenURI(retry + 1)

def get_random_nft(retry=0):
    """
    get data of random nft from saved nft collections
    """

    while True:
        try:
            collection = random.choice(NFT_COLLECTIONS)
            link = f'https://ipfs.io/ipfs/{collection["cid"]}/{random.randint(1,collection["supply"]-1)}'
            r = requests.get(link)

            return r.headers['X-Ipfs-Roots'].split(',')[-1]
        except Exception as err:
            logger.warning(f'cant get random nft ({retry}/{RETRY}): {err}')

            if retry < RETRY:
                time.sleep(10)
                retry += 1
            else:
                logger.error(f'Cant parse NFT in {retry} times, skip minting')
                list_send.append(f'{STR_CANCEL}Cant parse NFT in {retry} times, skip minting')
                return False

def make_modules_path(modules):
    new_lst = []
    for module in modules:
        try:
            tx_from, tx_to = TRANSACTIONS_COUNT[module.__name__]
            if module.__name__ == 'odos': tx_from = tx_to = 1
        except: tx_from = tx_to = 1
        for _ in range(random.randint(tx_from, tx_to)):
            new_lst.append(module)

    random.shuffle(new_lst)
    return new_lst

def get_proxy():
    if not USE_PROXY: return False
    if PROXY_DATA == '':
        proxy = random.choice(PROXIES)
        proxy_type = 'default'
    else:
        proxy = PROXY_DATA
        proxy_type = 'mobile'

    return {'proxy': proxy, 'type': proxy_type}

# ============== modules ==============

def approve_(amount, privatekey, chain, token_address, spender, retry=0):
    try:
        if amount == 0:
            logger.error(f'want to approve 0 tokens (token: {token_address}; spender: {spender})')
            return

        web3 = get_web3(chain, privatekey)

        spender = Web3.to_checksum_address(spender)

        wallet = web3.eth.account.from_key(privatekey).address
        contract, decimals, symbol = check_data_token(web3, token_address)

        ratio = random.randint(40, 400)

        module_str = f'approve: {int(amount * ratio) / 10 ** decimals} {symbol}'

        allowance_amount = check_allowance(chain, token_address, privatekey, spender)

        if amount > allowance_amount:

            contract_txn = contract.functions.approve(
                spender,
                int(amount * ratio)
            ).build_transaction(
                {
                    "chainId": web3.eth.chain_id,
                    "from": wallet,
                    "nonce": web3.eth.get_transaction_count(wallet),
                    'gasPrice': 0,
                    'gas': 0,
                    "value": 0
                }
            )

            contract_txn = add_gas_price(web3, contract_txn)
            contract_txn = add_gas_limit(web3, contract_txn)

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, 'approve')

            if status == 1:
                logger.success(f"{module_str} | {tx_link}")
                sleeping(15, 30)
            else:
                logger.error(f"{module_str} | tx is failed | {tx_link}")
                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

    except Exception as error:
        logger.error(f'{error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            approve_(amount, privatekey, chain, token_address, spender, retry + 1)

def get_the_most_balance(pk):
    stable_balances = {}
    for token in ['usdt', 'busd', 'usdc']:
        stable_balances[token] = check_balance(pk, 'zksync', ZKSYNC_TOKENS_CONTACT[token])
    most_token = max(stable_balances, key=stable_balances.get)
    logger.debug(f'find the most balance of stable: {stable_balances[most_token]} {most_token}')
    return most_token

def okx_withdraw(privatekey, CHAIN, retry=0):

    SYMBOL, amount_from, amount_to, account, SUB_ACC = value_okx()

    api_key         = OKX_KEYS[account]['api_key']
    secret_key      = OKX_KEYS[account]['api_secret']
    passphras       = OKX_KEYS[account]['password']

    wallet = evm_wallet(privatekey)

    # take FEE for withdraw
    _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}", meth="GET")
    response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10, headers=headers)
    for lst in response.json()['data']:
        if lst['chain'] == f'{SYMBOL}-{CHAIN}':
            FEE = lst['minFee']

    try:
        while True:
            if SUB_ACC == True:

                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/users/subaccount/list", meth="GET")
                list_sub =  requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10, headers=headers)
                list_sub = list_sub.json()

                for sub_data in list_sub['data']:
                    while True:
                        name_sub = sub_data['subAcct']

                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", meth="GET")
                        sub_balance = requests.get(f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",timeout=10, headers=headers)
                        sub_balance = sub_balance.json()
                        if sub_balance.get('msg') == f'Sub-account {name_sub} doesn\'t exist':
                            logger.warning(f'ERROR | {sub_balance["msg"]}')
                            continue
                        sub_balance = sub_balance['data'][0]['bal']

                        logger.info(f'{name_sub} | {sub_balance} {SYMBOL}')

                        if float(sub_balance) > 0:
                            body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2", "subAcct": name_sub}
                            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                            a = requests.post("https://www.okx.cab/api/v5/asset/transfer",data=str(body), timeout=10, headers=headers)
                        # time.sleep(1)
                        break

            try:
                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
                balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10, headers=headers)
                balance = balance.json()
                balance = balance["data"][0]["details"][0]["cashBal"]
                # print(balance)

                if balance != 0:
                    body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0", "subAcct": "", "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                    _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                    a = requests.post("https://www.okx.cab/api/v5/asset/transfer",data=str(body), timeout=10, headers=headers)
            except Exception as ex:
                pass


            # CHECK MAIN BALANCE
            _, _, headers = okx_data(api_key, secret_key, passphras,
                                     request_path=f"/api/v5/asset/balances?ccy={SYMBOL}", meth="GET")
            main_balance = requests.get(f'https://www.okx.cab/api/v5/asset/balances?ccy={SYMBOL}', timeout=10,
                                        headers=headers)
            main_balance = main_balance.json()
            main_balance = float(main_balance["data"][0]['availBal'])
            logger.info(f'total balance | {main_balance} {SYMBOL}')

            if amount_from > main_balance:
                logger.warning(f'not enough balance ({main_balance} < {amount_from}), waiting 10 secs...')
                time.sleep(10)
                continue

            if amount_to > main_balance:
                logger.warning(f'you want to withdraw MAX {amount_to} but have only {round(main_balance, 7)}')
                amount_to = round(main_balance, 7)

            AMOUNT = round(random.uniform(amount_from, amount_to), 7)
            break




        body = {"ccy":SYMBOL, "amt":AMOUNT, "fee":FEE, "dest":"4", "chain":f"{SYMBOL}-{CHAIN}", "toAddr":wallet}
        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal", meth="POST", body=str(body))
        a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal",data=str(body), timeout=10, headers=headers)
        result = a.json()
        # cprint(result, 'blue')

        if result['code'] == '0':
            logger.success(f"withdraw success => {wallet} | {AMOUNT} {SYMBOL}")
            list_send.append(f'{STR_DONE}okx_withdraw | {AMOUNT} {SYMBOL}')
            return AMOUNT
        else:
            error = result['msg']
            logger.error(f"withdraw unsuccess => {wallet} | error : {error}")
            if retry < RETRY:
                return okx_withdraw(privatekey, CHAIN, retry)
            else:
                list_send.append(f"{STR_CANCEL}okx_withdraw :  {result['msg']}")

    except Exception as error:
        logger.error(f"withdraw unsuccess => {wallet} | error : {error}")
        if retry < RETRY:
            logger.info(f"try again in 10 sec. => {wallet}")
            sleeping(10, 10)
            if 'Insufficient balance' in str(error): return okx_withdraw(privatekey, CHAIN, retry)
            return okx_withdraw(privatekey, CHAIN, retry)
        else:
            list_send.append(f'{STR_CANCEL}okx_withdraw')

def transfer(pk, chain, retry=0):
    while True:
        try:


            keep_from, keep_to = value_keep_transfer()

            web3 = get_web3(chain, pk)
            wallet = web3.eth.account.from_key(pk).address

            human_balance = check_balance(pk, chain) - random.uniform(keep_from, keep_to)
            balance = int(human_balance * 10 ** 18)

            to = web3.to_checksum_address(RECIPIENTS_WALLETS[pk])

            module_str = f'transfer {round(human_balance, 6)} ETH => {to}'

            tx = {
                'value': balance,
                'from': wallet,
                'to': to,
                'nonce': web3.eth.get_transaction_count(wallet),
                'gasPrice': web3.eth.gas_price
            }
            tx['gas'] = web3.eth.estimate_gas(tx)

            # смотрим газ, если выше выставленного значения : спим
            total_fee = int(tx['gas'] * tx['gasPrice'])
            is_fee = checker_total_fee(chain, total_fee)

            if is_fee == False: continue

            tx_hash = sign_tx(web3, tx, pk)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, f'transfer eth')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                break
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    retry += 1
                    continue
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    break

        except Exception as error:
            logger.error(f'{module_str} | {error}')
            if retry < RETRY:
                retry += 1
                sleeping(10, 20)
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                break

def orbiter_bridge(privatekey, from_chain, to_chain, retry=0):
    try:
        if to_chain == 'zksync_lite':
            keep_values = value_orbiter()
            transfer_from = keep_values[to_chain]['transfer_from']
            transfer_to = keep_values[to_chain]['transfer_to']
            amount_to_bridge = round(random.uniform(transfer_from, transfer_to), 8)
        elif to_chain == 'arbitrum':
            keep_from, keep_to = value_across()
            balance = check_balance(privatekey, from_chain)
            keep = round(random.uniform(keep_from, keep_to), 8)

            amount_to_bridge = balance - keep

        module_str = f'orbiter_bridge : {from_chain} => {to_chain}'

        min_bridge, max_bridge, fees = check_orbiter_limits(from_chain, to_chain)
        min_bridge = min_bridge + fees

        amount = get_orbiter_value(amount_to_bridge, to_chain, from_chain) # получаем нужный amount

        module_str = f'orbiter_bridge : {from_chain} {amount} ETH => {to_chain}'
        logger.info(module_str)

        if min_bridge <= amount <= max_bridge:

            web3 = get_web3(from_chain, privatekey)
            account = web3.eth.account.from_key(privatekey)
            wallet = account.address

            if from_chain == 'zksync_lite':
                zk_lite_transfer(privatekey, '0xe4edb277e41dc89ab076a1f049f4a3efa700bce8', amount)

            else:
                value = intToDecimal(amount, 18)

                chain_id    = web3.eth.chain_id
                nonce       = web3.eth.get_transaction_count(wallet)


                if from_chain == 'zksync':
                    to_contract = '0xE4eDb277e41dc89aB076a1F049f4a3EfA700bCE8'
                else:
                    to_contract = '0x80C67432656d59144cEFf962E8fAF8926599bCF8'

                contract_txn = {
                    'chainId': chain_id,
                    'nonce': nonce,
                    'from': wallet,
                    'to': to_contract,
                    'value': value,
                    'gas': 0,
                    'gasPrice': 0
                }

                if from_chain == 'bsc':
                    contract_txn['gasPrice'] = random.randint(1000000000, 1050000000) # специально ставим 1 гвей, так транза будет дешевле
                else:
                    contract_txn = add_gas_price(web3, contract_txn)
                contract_txn = add_gas_limit(web3, contract_txn)

                if from_chain == 'zksync': divider = DIVIDERS['orbiter']
                else: divider = 1
                contract_txn['gas'] = int(contract_txn['gas'] / divider)

                # смотрим газ, если выше выставленного значения : спим
                total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee      = checker_total_fee(from_chain, total_fee)

                if is_fee == True:

                    tx_hash = sign_tx(web3, contract_txn, privatekey)
                    tx_link = f'{DATA[from_chain]["scan"]}/{tx_hash}'

                    status = check_status_tx(from_chain, tx_hash, 'orbiter bridge')
                    if status == 1:
                        logger.success(f'{module_str} | {tx_link}')
                        list_send.append(f'{STR_DONE}{module_str}')

                    else:
                        logger.error(f'{module_str} | tx is failed | {tx_link}')
                        if retry < RETRY:
                            orbiter_bridge(privatekey, from_chain, to_chain, retry+1)
                        else:
                            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

                else:
                    orbiter_bridge(privatekey, from_chain, to_chain, retry)

        else:

            if amount < min_bridge:

                logger.error(f"{module_str} : can't bridge : {amount} (amount) < {min_bridge} (min_bridge)")
                list_send.append(f'{STR_CANCEL}{module_str} : {amount} < {min_bridge}')

            elif amount > max_bridge:

                logger.error(f"{module_str} : can't bridge : {amount} (amount) > {max_bridge} (max_bridge)")
                list_send.append(f'{STR_CANCEL}{module_str} : {amount} > {max_bridge}')

    except Exception as error:
        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            logger.info(f'try again | {wallet}')
            sleeping(10, 10)
            orbiter_bridge(privatekey, from_chain, to_chain, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def bridge_eth_to_zksync(privatekey, retry=0):

    try:
        keep_from, keep_to = value_zksync_bridge()
        keep = random.uniform(keep_from, keep_to)

        module_str = f'bridge Ethereum -> zkSync Era'
        logger.info(module_str)

        chain = 'ethereum'

        gas_limit_l2    = random.randint(733000, 740000)
        gasPerPubdata   = 800   

        web3 = get_web3(chain, privatekey)

        wallet = web3.eth.account.from_key(privatekey).address
        
        contract = web3.eth.contract(address='0x32400084C286CF3E17e7B677ea9583e60a000324', abi=ABI_BRIDGE_ZKSYNC)
        
        base_cost = contract.functions.l2TransactionBaseCost(web3.eth.gas_price, gas_limit_l2, gasPerPubdata).call()

        for i in range(2): # to get gas in first time and in second make `balance - gas` to send whole balance
            if i == 0:
                amount_ = 0.0001
            else:
                balance = check_balance(privatekey, 'ethereum')
                amount_ = balance - keep - (total_fee / 10 ** 18 * 1.5)

            amount = Web3.to_wei(amount_, 'ether')
            value = amount + base_cost

            object_tx = contract.functions.requestL2Transaction(
                wallet, amount, bytes(), gas_limit_l2, gasPerPubdata, [], wallet
            )

            contract_txn = object_tx.build_transaction({
                'chainId': web3.eth.chain_id,
                'from': wallet,
                'value': value,
                'nonce': web3.eth.get_transaction_count(wallet),
                'gasPrice': web3.eth.gas_price,
                'gas': 250000
            })
            contract_txn['gas'] = web3.eth.estimate_gas(contract_txn)

            # смотрим газ, если выше выставленного значения : спим
            total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])

        is_fee      = checker_total_fee(chain, total_fee)
        if is_fee == True:

            tx_hash     = sign_tx(web3, contract_txn, privatekey)
            tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, 'bridge to zksync')
            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    bridge_eth_to_zksync(privatekey, retry + 1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

        else:
            bridge_eth_to_zksync(privatekey)


    except Exception as error:
        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            logger.info(f'try again | {wallet}')
            sleeping(10, 10)
            bridge_eth_to_zksync(privatekey, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def syncswap_eth_pool(privatekey, token, retry=0):

    try:

        module_str = f'SyncSwap : pool eth-{token}'
        logger.info(module_str)

        chain = 'zksync'

        amount_from, amount_to, amount_token_from, amount_token_to, eth_to_pool_from, eth_to_pool_to, token_to_pool_from, token_to_pool_to, tokens, make_pool = value_syncswap()

        amount = round(random.uniform(eth_to_pool_from, eth_to_pool_to), 8)
        eth_spend_value  = intToDecimal(amount, 18)

        SYNCSWAP_ROUTER_CONTRACT_ADDRESS    = Web3.to_checksum_address("0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295")
        ZERO_ADDR                           = Web3.to_checksum_address('0x0000000000000000000000000000000000000000')
        syncswap_token_contract             = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token])
        syncswap_pool                       = Web3.to_checksum_address(SYNCSWAP_POOLS[token])

        token_ratio = random.uniform(token_to_pool_from, token_to_pool_to)
        amount_to_pool = int(check_balance(privatekey, chain, syncswap_token_contract, human=False) * token_ratio)

        if amount_to_pool > 0:

            web3 = get_web3(chain, privatekey)

            token_contract, token_decimal, symbol = check_data_token(web3, syncswap_token_contract)

            wallet = web3.eth.account.from_key(privatekey).address

            approve_(amount_to_pool, privatekey, chain, syncswap_token_contract, SYNCSWAP_ROUTER_CONTRACT_ADDRESS, retry=0)

            pool_contract = web3.eth.contract(address=SYNCSWAP_ROUTER_CONTRACT_ADDRESS, abi=ABI_SWAP_SYNCSWAP)
            
            nonce = web3.eth.get_transaction_count(wallet)

            data = abi.encode(['address'], [wallet])
            minLiquidity = Web3.to_int(0)
            callback = ZERO_ADDR
            callbackData = '0x' # call back data

            inputs = [{
                'token' : ZERO_ADDR, 
                'amount' : int(eth_spend_value)
            },
            {
                'token' : syncswap_token_contract, 
                'amount' : amount_to_pool
            }]

            contract_txn = pool_contract.functions.addLiquidity2(
            syncswap_pool,
            inputs,
            data,
            minLiquidity,
            callback,
            callbackData
            ).build_transaction({
            'from': wallet,
            # "gas": 20000000, 
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce,
            "value": eth_spend_value
            })

            contract_txn['gas'] = int(contract_txn['gas'] / DIVIDERS['syncswap_pool'])

            # cprint(contract_txn, 'white')

            # смотрим газ, если выше выставленного значения : спим
            total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
            is_fee      = checker_total_fee(chain, total_fee)

            if is_fee == True: 

                tx_hash     = sign_tx(web3, contract_txn, privatekey)
                tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, 'add to pool')
                
                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                    sleeping(20,50)
                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        syncswap_eth_pool(privatekey, token, retry+1)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

            else:
                syncswap_eth_pool(privatekey, token, retry)

        else:
            logger.error(f'balance of {token}: {amount_to_pool}')
            list_send.append(f'{STR_CANCEL}{module_str}')

    except Exception as error:
        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            sleeping(10,20)
            syncswap_eth_pool(privatekey, token, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def syncswap_swap(privatekey, retry=0):

    amount_from, amount_to, amount_token_from, amount_token_to, eth_to_pool_from, eth_to_pool_to, token_to_pool_from, token_to_pool_to, tokens, make_pool = value_syncswap()


    token = random.choice(tokens)

    for from_token, to_token in zip(['eth', token], [token, 'eth']):
        while True:
            try:
                module_str = f'SyncSwap : swap {from_token} => {to_token}'
                logger.info(module_str)

                chain = 'zksync'

                web3 = get_web3(chain, privatekey)
                wallet = web3.eth.account.from_key(privatekey).address
                nonce = web3.eth.get_transaction_count(wallet)

                contract = web3.eth.contract(
                    address=web3.to_checksum_address("0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295"),
                    abi=ABI_SWAP_SYNCSWAP)

                from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[from_token])

                if from_token == 'eth':
                    old_balance = check_balance(privatekey, chain, ZKSYNC_TOKENS_CONTACT[to_token])

                    amount = round(random.uniform(amount_from, amount_to), 8)
                    value  = intToDecimal(amount, 18)

                    synkswap_pool = web3.to_checksum_address(SYNCSWAP_POOLS[to_token])
                else:
                    value = int(check_balance(privatekey, chain, from_token_address, human=False) * random.uniform(amount_token_from, amount_token_to))

                    approve_(value, privatekey, chain, from_token_address, contract.address)
                    synkswap_pool = web3.to_checksum_address(SYNCSWAP_POOLS[from_token])


                tokenIn = '0x0000000000000000000000000000000000000000' if from_token == 'eth' else from_token_address

                steps = [{
                            'pool' : synkswap_pool, # pool
                            'data' : abi.encode(['address', 'address', 'uint8'], [from_token_address, wallet, 1]),
                            'callback' : Web3.to_checksum_address('0x00D68275e71B094ea0248De15ee3013465872eb9'), # call back
                            'callbackData' : '0x' # call back data
                }]

                min_out = Web3.to_int(0)
                deadline = int(time.time()) + 1000000

                paths = [{
                    'steps': steps,
                    'tokenIn': tokenIn,
                    'amountIn': value
                }]

                contract_txn = contract.functions.swap(
                paths,
                min_out,
                deadline
                ).build_transaction({
                'from': wallet,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'value': value
                })

                contract_txn['gas'] = int(contract_txn['gas'] / DIVIDERS['syncswap_swap'])

                # смотрим газ, если выше выставленного значения : спим
                total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee      = checker_total_fee(chain, total_fee)

                if is_fee == True:

                    tx_hash     = sign_tx(web3, contract_txn, privatekey)
                    tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                    status = check_status_tx(chain, tx_hash, 'swap')

                    if status == 1:
                        logger.success(f'{module_str} | {tx_link}')
                        list_send.append(f'{STR_DONE}{module_str}')
                        retry = 0

                        if from_token == 'eth':
                            wait_balance(privatekey, chain, old_balance + 0.000001, ZKSYNC_TOKENS_CONTACT[to_token])
                            sleeping(15, 40)
                            if make_pool == True:
                                syncswap_eth_pool(privatekey, token)
                        break

                    else:
                        logger.error(f'{module_str} | tx is failed | {tx_link}')
                        if retry < RETRY:
                            retry += 1
                            continue
                        else:
                            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                            break
                else:
                    continue

            except Exception as error:
                logger.error(f'{module_str}: {error}')
                if retry < RETRY:
                    sleeping(10,20)
                    retry += 1
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    retry = 0
                    return

def muteswap_pool(pk, token, retry=0):

    while True:
        try:
            amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool = value_muteswap()

            chain = 'zksync'

            module_str = f'MuteSwap : pool eth-{token}'
            logger.info(module_str)

            web3 = get_web3(chain, pk)
            wallet = web3.eth.account.from_key(pk).address

            to_token_address = web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token])
            balance = check_balance(pk, chain, to_token_address, human=False)

            token_ratio = random.uniform(token_to_pool_from, token_to_pool_to)
            amount_token = int(balance * token_ratio)

            approve_(amount_token, pk, chain, to_token_address, '0x8b791913eb07c32779a16750e3868aa8495f5964')

            lp_contract = web3.eth.contract(address=web3.to_checksum_address(MUTESWAP_POOLS[token]),abi=ABI_MUTESWAP_LP)
            eth_amount = lp_contract.functions.current(to_token_address, amount_token).call()

            pool_contract = web3.eth.contract(address=web3.to_checksum_address('0x8b791913eb07c32779a16750e3868aa8495f5964'), abi=ABI_MUTESWAP_POOL)

            tx = pool_contract.functions.addLiquidityETH(
                to_token_address,
                amount_token,
                int(amount_token * 0.99),
                int(eth_amount*0.99),
                wallet,
                int(time.time())+1000,
                50,
                False
            ).build_transaction({
                    'value': eth_amount,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gas': 0,
                    'gasPrice': 0
                })

            contract_txn    = add_gas_price(web3, tx)
            gasLimit        = web3.eth.estimate_gas(contract_txn)
            contract_txn['gas'] = int(gasLimit / DIVIDERS['mute_swap'])

            # смотрим газ, если выше выставленного значения : спим
            total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
            is_fee      = checker_total_fee(chain, total_fee)

            if is_fee   == False: continue

            tx_hash     = sign_tx(web3, contract_txn, pk)
            tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, f'muteswap pool eth-{token}')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')

                sleeping(15, 60)
                break

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    retry += 1
                    continue
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    break

        except Exception as error:
            logger.error(f'{module_str} | {error}')
            if retry < RETRY:
                retry += 1
                sleeping(10,20)
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                break

def mute_swap(privatekey, forced_token=False, retry=0):
    """
    :param forced_token:
    force swap all balance of `forced_token` to eth
    """

    amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool = value_muteswap()

    if forced_token == False: token = random.choice(tokens)
    else:
        token = forced_token
        amount_token_from = 1
        amount_token_to = 1

    stable_pool = False

    chain = 'zksync'
    web3 = get_web3(chain, privatekey)
    wallet = web3.eth.account.from_key(privatekey).address

    contract = web3.eth.contract(address=Web3.to_checksum_address("0x8B791913eB07C32779a16750e3868aA8495F5964"),
                                 abi=ABI_SWAP_MUTE)

    for from_token, to_token in zip(['eth', token], [token, 'eth']):
        if forced_token != False and from_token == 'eth': continue
        while True:
            try:

                module_str = f'MuteSwap : swap {from_token} => {to_token}'
                logger.info(module_str)

                from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[from_token])
                to_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[to_token])

                if from_token == 'eth':
                    amount = round(random.uniform(amount_from, amount_to), 8)
                    value  = intToDecimal(amount, 18)
                    old_balance = check_balance(privatekey, chain, to_token_address)
                else:
                    value = int(check_balance(privatekey, chain, from_token_address, human=False) * random.uniform(amount_token_from, amount_token_to))

                path        = [from_token_address, to_token_address]

                fees = contract.functions.getAmountOut(
                    value,
                    path[0],
                    path[1]
                ).call()

                amountOutMin = int(fees[0] * (100 - slippage * 2) / 100)

                if from_token == 'eth':
                    contract_txn = contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                        amountOutMin,
                        path,
                        wallet,
                        int(time.time() + 1000),
                        [False, False]
                        ).build_transaction({
                        'value': value,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gas': 0,
                        'gasPrice': 0
                    })
                else:
                    approve_(value, privatekey, chain, from_token_address, contract.address)

                    contract_txn = contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                        value,
                        amountOutMin,
                        path,
                        wallet,
                        int(time.time() + 1000),
                        [stable_pool, False]
                    ).build_transaction({
                        'value': 0,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gas': 0,
                        'gasPrice': 0
                    })

                contract_txn    = add_gas_price(web3, contract_txn)
                gasLimit        = web3.eth.estimate_gas(contract_txn)
                contract_txn['gas'] = int(gasLimit / DIVIDERS['mute_swap'])

                # смотрим газ, если выше выставленного значения : спим
                total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee      = checker_total_fee(chain, total_fee)

                if is_fee   == False: continue

                tx_hash     = sign_tx(web3, contract_txn, privatekey)
                tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'muteswap {from_token}-{to_token}')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                    retry = 0

                    if from_token == 'eth':
                        wait_balance(privatekey, chain, old_balance + 0.000001, to_token_address)
                        sleeping(15, 60)
                        if make_pool == True:
                            muteswap_pool(privatekey, token)
                    elif forced_token: sleeping(15,60)

                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                sleeping(10,20)
                if retry < RETRY:
                    retry += 1
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    return

def space_swap(privatekey, needed_usdc=False, retry=0):

        amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool = value_spaceswap()

        if needed_usdc:
            token = 'usdc'
        else:
            token = random.choice(tokens)

        chain = 'zksync'
        web3 = get_web3(chain, privatekey)
        wallet = web3.eth.account.from_key(privatekey).address

        contract = web3.eth.contract(address=Web3.to_checksum_address("0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d"), abi=SPACE_ABI)

        for from_token, to_token in zip(['eth', token], [token, 'eth']):
            if needed_usdc and from_token != 'eth': continue
            while True:
                try:

                    module_str = f'SpaceSwap : swap {from_token} => {to_token}'
                    logger.info(module_str)

                    from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[from_token])
                    to_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[to_token])

                    if needed_usdc:
                        old_balance = check_balance(privatekey, chain, to_token_address)

                        amounts = contract.functions.getAmountsIn(
                            needed_usdc,
                            [
                                from_token_address,
                                to_token_address
                            ]
                        ).call() # response [eth_input_value, token_output_value]
                        value = int(amounts[0] / (1 - slippage * 1.75 / 100))
                    else:
                        if from_token == 'eth':
                            old_balance = check_balance(privatekey, chain, to_token_address)
                            amount = round(random.uniform(amount_from, amount_to), 8)
                            value  = intToDecimal(amount, 18)
                        else:
                            value = int(
                                check_balance(privatekey, chain, from_token_address, human=False)
                                * round(random.uniform(amount_token_from, amount_token_to))
                            )

                    path        = [from_token_address, to_token_address]
                    fees = contract.functions.getAmountsOut(
                        value,
                        [path[0],
                        path[1]]
                    ).call()

                    amountOutMin = int(fees[1] * (100 - slippage * 2) / 100)

                    if from_token == 'eth':
                        contract_txn = contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                            amountOutMin,
                            path,
                            wallet,
                            int(time.time() + 1000),
                            ).build_transaction({
                            'value': value,
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gas': 0,
                            'gasPrice': 0,
                        })
                    else:
                        approve_(value, privatekey, chain, from_token_address, contract.address)

                        contract_txn = contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                            value,
                            amountOutMin,
                            path,
                            wallet,
                            int(time.time() + 1000),
                        ).build_transaction({
                            'value': 0,
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gas': 0,
                            'gasPrice': 0,
                        })


                    contract_txn    = add_gas_price(web3, contract_txn)
                    gasLimit        = web3.eth.estimate_gas(contract_txn)
                    contract_txn['gas'] = int(gasLimit / DIVIDERS['space_swap'])

                    # смотрим газ, если выше выставленного значения : спим
                    total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                    is_fee      = checker_total_fee(chain, total_fee)
                    if is_fee   == False: continue

                    tx_hash     = sign_tx(web3, contract_txn, privatekey)
                    tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                    status = check_status_tx(chain, tx_hash, f'SpaceSwap {from_token}-{to_token}')

                    if status == 1:
                        logger.success(f'{module_str} | {tx_link}')
                        list_send.append(f'{STR_DONE}{module_str}')
                        retry = 0

                        if from_token == 'eth':
                            wait_balance(privatekey, chain, old_balance + 0.000001, to_token_address)
                            sleeping(15, 60)

                            if not needed_usdc:
                                if to_token == 'space':
                                    convert_space(privatekey)
                                elif to_token == 'usdc' and make_pool == True:
                                    space_pool(privatekey, token)
                        break

                    else:
                        logger.error(f'{module_str} | tx is failed | {tx_link}')
                        if retry < RETRY:
                            retry += 1
                            continue
                        else:
                            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                            break

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return

def space_pool(pk, token, retry=0):
    while True:
        try:
            amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool = value_spaceswap()

            chain = 'zksync'

            module_str = f'SpaceSwap : pool eth-{token}'
            logger.info(module_str)

            web3 = get_web3(chain, pk)
            wallet = web3.eth.account.from_key(pk).address

            to_token_address = web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token])
            balance = check_balance(pk, chain, to_token_address, human=False)

            token_ratio = random.uniform(token_to_pool_from, token_to_pool_to)
            amount_token = int(balance * token_ratio)

            approve_(amount_token, pk, chain, to_token_address, '0xbe7d1fd1f6748bbdefc4fbacafbb11c6fc506d1d')

            pool_contract = web3.eth.contract(address=web3.to_checksum_address('0xbe7d1fd1f6748bbdefc4fbacafbb11c6fc506d1d'), abi=SPACE_ABI)

            eth_amount = pool_contract.functions.getAmountsOut(
                amount_token,
                [
                    web3.to_checksum_address(to_token_address),
                    web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT['eth']),
                ]
            ).call()[1]

            contract_txn = pool_contract.functions.addLiquidityETH(
                to_token_address,
                amount_token,
                int(amount_token * 0.99),
                int(eth_amount * 0.99),
                wallet,
                int(time.time())+1000,
            ).build_transaction({
                    'value': eth_amount,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price
                })

            # смотрим газ, если выше выставленного значения : спим
            total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
            is_fee      = checker_total_fee(chain, total_fee)

            if is_fee   == False: continue

            tx_hash     = sign_tx(web3, contract_txn, pk)
            tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, f'spaceswap pool eth-{token}')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                sleeping(15, 60)
                break

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    retry += 1
                    continue
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    break

        except Exception as error:
            logger.error(f'{module_str} | {error}')
            if retry < RETRY:
                retry += 1
                sleeping(10,20)
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                break

def convert_space(pk, retry=0):

    amount_from, amount_to = value_space_convert()

    chain = 'zksync'
    web3 = get_web3(chain, pk)
    wallet = web3.eth.account.from_key(pk).address

    contract = web3.eth.contract(web3.to_checksum_address("0x6aF43486Cb84bE0e3EDdCef93d3C43Ef0C5F63b1"), abi=SPACE_CONVERTER_ABI)

    for from_token, to_token in zip(['space', 'stake', 'xspace'], ['xspace', 'xspace', 'space']):
        while True:
            try:

                module_str = f'SpaceSwap Convert : {from_token} - {to_token}'
                logger.info(module_str)

                if from_token == 'stake':
                    from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT['xspace'])
                else:
                    from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[from_token])

                value = check_balance(pk, chain, from_token_address, human=False)
                percent = random.randint(amount_from, amount_to) / 100

                # 1. convert SPACE -> xSPACE
                if from_token == 'space':
                    approve_(value, pk, chain, from_token_address, contract.address)

                    contract_tx = contract.functions.convert(int(value * percent)).build_transaction({
                        # "chainId": web3.eth.chain_id,
                        'value': 0,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gas': 0,
                        'gasPrice': 0,
                    })

                # 2. stake XSPACE
                elif from_token == 'stake':
                    contract_tx = contract.functions.redeem(value, 1).build_transaction({
                        # "chainId": web3.eth.chain_id,
                        'value': 0,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gas': 0,
                        'gasPrice': 0,
                    })

                # 3. unstake XSPACE and get SPACE
                else:
                    contract_tx = contract.functions.finalizeRedeem(0).build_transaction({
                        # "chainId": web3.eth.chain_id,
                        'value': 0,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gas': 0,
                        'gasPrice': 0,
                    })


                contract_tx = add_gas_price(web3, contract_tx)
                gasLimit = web3.eth.estimate_gas(contract_tx)
                contract_tx['gas'] = int(gasLimit / DIVIDERS['space_swap'])

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(contract_tx['gas'] * contract_tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, contract_tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'spaceswap {from_token}-{to_token}')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                    retry = 0
                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    return

def bridge_to_eth_from_era(privatekey, retry=0):
    try:
        amount_from, amount_to = value_era_to_eth()

        module_str = f'bridge to ethereum from era'
        logger.info(module_str)
        chain = 'zksync'

        web3 = get_web3(chain, privatekey)
        wallet = web3.eth.account.from_key(privatekey).address
        contract = web3.eth.contract(address=web3.to_checksum_address('0x000000000000000000000000000000000000800A'), abi=ZKSYNC_ERA_BRIDGE)

        value = int(round(random.uniform(amount_from, amount_to), 7) * 10 ** 18)

        contract_txn = contract.functions.withdraw(wallet).build_transaction({
            'from': wallet,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(wallet),
            'value': value,
        })

        contract_txn['gas'] = int(contract_txn['gas'] / DIVIDERS['bridge_to_eth'])

        # смотрим газ, если выше выставленного значения : спим
        total_fee = int(contract_txn['gas'] * contract_txn['gasPrice'])


        is_fee = checker_total_fee(chain, total_fee)
        if is_fee == True:

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, 'bridge from era to eth')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    bridge_to_eth_from_era(privatekey, retry + 1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
        else:
            bridge_to_eth_from_era(privatekey)


    except Exception as error:
        logger.error(f'{module_str}: {error}')
        if retry < RETRY:
            sleeping(10,20)
            bridge_to_eth_from_era(privatekey, retry + 1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def merkly(pk):
    def merkly_mint(pk, retry=0):
        try:
            module_str = 'merkly nft mint'
            logger.info(module_str)

            cost = contract.functions.cost().call()
            tx = contract.functions.mint().build_transaction({
                    "chainId": web3.eth.chain_id,
                    'value': cost,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gas': 0,
                    'gasPrice': 0,
                })
            contract_tx = add_gas_price(web3, tx)
            contract_tx['gas'] = web3.eth.estimate_gas(contract_tx)

            total_fee = int(contract_tx['gas'] * contract_tx['gasPrice'])
            is_fee = checker_total_fee(chain, total_fee)
            if is_fee == False: return merkly_mint(pk)

            tx_hash = sign_tx(web3, contract_tx, pk)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, f'merkly mint')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                sleeping(15, 60)

                tx_info = web3.eth.get_transaction_receipt(tx_hash)
                hex_nft_id = tx_info['logs'][-2]['topics'][-1].hex()
                return int(hex_nft_id, 16)
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    time.sleep(10)
                    return merkly_mint(pk, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    return False
        except Exception as error:
            logger.error(f'{module_str} | {error}')
            if retry < RETRY:
                sleeping(10, 20)
                return merkly_mint(pk, retry + 1)
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                return False

    def merkly_bridge(pk, nft_id, retry=0):
        try:
            chains = value_merkly()
            to_chain = random.choice(chains)

            module_str = f'merkly nft bridge to {to_chain}'
            logger.info(module_str)


            fee = int(contract.functions.estimateFees(CHAINS_ID[to_chain], nft_id).call() + 1)
            contract_tx = contract.functions.crossChain(CHAINS_ID[to_chain], nft_id).build_transaction({
                    # "chainId": web3.eth.chain_id,
                    'value': fee,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

            total_fee = int(contract_tx['gas'] * contract_tx['gasPrice'])
            is_fee = checker_total_fee(chain, total_fee)
            if is_fee == False: return merkly_mint(pk)

            tx_hash = sign_tx(web3, contract_tx, pk)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, f'merkly bridge to {to_chain}')

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                sleeping(15, 60)
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    time.sleep(10)
                    return merkly_bridge(pk, nft_id, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    return False
        except Exception as error:
            logger.error(f'{module_str} | {error}')
            if retry < RETRY:
                sleeping(10, 20)
                return merkly_bridge(pk, nft_id, retry+1)
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                return False


    chain = 'zksync'

    web3 = get_web3(chain, pk)
    wallet = web3.eth.account.from_key(pk).address
    contract = web3.eth.contract(address=web3.to_checksum_address('0x0BF0d6260fb4f4FC77b143eaFF9E4Fe51dD08C83'), abi=MERKLY_ABI)

    nft_id = merkly_mint(pk)
    if not nft_id: return
    merkly_bridge(pk, nft_id)

def velocore_swap(pk, retry=0):

    def velocore_bridge(pk, token_to_pool_from, token_to_pool_to, retry=0):

        pool_contract = web3.eth.contract(address=web3.to_checksum_address('0xb3120ad6c3285fc4e422581d9ad003277802cc47'), abi=VELOCORE_POOL_ABI)
        pool_token_contract = web3.eth.contract(address=web3.to_checksum_address('0xcd52cbc975fbb802f82a1f92112b1250b5a997df'),abi=VELOCORE_PAIR_ABI) # USDC-WETH

        while True:
            try:

                module_str = f'Velocore : pool {from_token}-{to_token}'

                ratio = random.uniform(token_to_pool_from, token_to_pool_to)
                amount_token_to_pool = int(check_balance(pk, chain, to_token_address, human=False) * ratio)
                amount_eth_to_pool = pool_token_contract.functions.getAmountOut(amount_token_to_pool, to_token_address).call()
                is_stable = pool_token_contract.functions.stable().call()

                human_value_token = round(Decimal(amount_token_to_pool / 10 ** to_decimals), 8)
                human_value_eth = round(Decimal(amount_eth_to_pool / 10 ** 18), 8)

                module_str = f'Velocore : pool {human_value_token} {from_token} + {human_value_eth} {to_token}'
                logger.info(module_str)

                approve_(amount_token_to_pool, pk, chain, to_token_address, contract.address)

                contract_txn = contract.functions.addLiquidityETH(
                    to_token_address,
                    is_stable,
                    amount_token_to_pool,
                    int(amount_token_to_pool * (1 - slippage / 100)),
                    int(amount_eth_to_pool * (1 - slippage / 100)),
                    wallet,
                    int((time.time() + 300) * 10 ** 4)  # + 5 min
                ).build_transaction({
                    'chainId': web3.eth.chain_id,
                    'value': amount_eth_to_pool,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee      = checker_total_fee(chain, total_fee)

                if is_fee   == False: continue

                tx_hash     = sign_tx(web3, contract_txn, pk)
                tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'velocore pool {from_token} + {to_token}')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')

                    sleeping(15, 60)
                    # STAKE
                    while True:
                        module_str = f'Velocore : stake {from_token}-{to_token}'
                        try:
                            pool_token_balance = pool_token_contract.functions.balanceOf(wallet).call()
                            approve_(pool_token_balance, pk, chain, pool_token_contract.address, pool_contract.address)

                            contract_txn = pool_contract.functions.deposit(pool_token_balance, 0).build_transaction({
                                'chainId': web3.eth.chain_id,
                                'value': 0,
                                'from': wallet,
                                'nonce': web3.eth.get_transaction_count(wallet),
                                'gasPrice': web3.eth.gas_price,
                            })

                            # смотрим газ, если выше выставленного значения : спим
                            total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                            is_fee      = checker_total_fee(chain, total_fee)

                            if is_fee   == False: continue

                            tx_hash     = sign_tx(web3, contract_txn, pk)
                            tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                            status = check_status_tx(chain, tx_hash, f'velocore stake {from_token} + {to_token}')

                            if status == 1:
                                logger.success(f'{module_str} | {tx_link}')
                                list_send.append(f'{STR_DONE}{module_str}')

                                sleeping(15, 60)
                                break
                        except Exception as error:
                            logger.error(f'{module_str} | {error}')
                            if retry < RETRY:
                                retry += 1
                                sleeping(10, 20)
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str}')
                                break
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    return


    amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage, token_to_pool_from, token_to_pool_to, make_pool = value_velocore()
    token = random.choice(tokens)

    chain = 'zksync'
    web3 = get_web3(chain)
    wallet = web3.eth.account.from_key(pk).address
    contract = web3.eth.contract(address=Web3.to_checksum_address("0xd999E16e68476bC749A28FC14a0c3b6d7073F50c"),abi=VELOCORE_ABI)

    for from_token, to_token in zip(['eth', token], [token, 'eth']):
        while True:
            try:

                module_str = f'Velocore : swap {from_token} => {to_token}'
                logger.info(module_str)

                from_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[from_token])
                to_token_address = Web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[to_token])

                _, from_decimals, _ = check_data_token(web3, from_token_address)
                _, to_decimals, _ = check_data_token(web3, to_token_address)


                if from_token == 'eth':
                    amount = round(random.uniform(amount_from, amount_to), 8)
                    value = int(amount * 10 ** 18)
                    old_balance = check_balance(pk, chain, to_token_address)
                else:
                    value = int(check_balance(pk, chain, from_token_address, human=False) * random.uniform(amount_token_from, amount_token_to))

                amount_out, stable = contract.functions.getAmountOut(
                    value,
                    from_token_address,
                    to_token_address,
                ).call()
                amount_out_min = int(amount_out * (1 - slippage / 100))

                human_value_from = round(Decimal(value / 10 ** from_decimals), 8)
                human_value_to = round(Decimal(amount_out_min / 10 ** to_decimals), 8)

                if from_token == 'eth':
                    tx = contract.functions.swapExactETHForTokens(
                        amount_out_min,
                        [(from_token_address, to_token_address, stable)],
                        wallet,
                        int((time.time() + 300) * 10 ** 4) # + 5 min
                    )
                    tx_value = value
                else:
                    approve_(value, pk, chain, from_token_address, contract.address)

                    tx = contract.functions.swapExactTokensForETH(
                        value,
                        amount_out_min,
                        [(from_token_address, to_token_address, stable)],
                        wallet,
                        int((time.time() + 300) * 10 ** 4)  # + 5 min
                    )
                    tx_value = 0

                contract_txn = tx.build_transaction({
                    'chainId': web3.eth.chain_id,
                    'value': tx_value,
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee   = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee      = checker_total_fee(chain, total_fee)

                if is_fee   == False: continue

                tx_hash     = sign_tx(web3, contract_txn, pk)
                tx_link     = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'velocore {human_value_from} {from_token} -> {human_value_to} {to_token}')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                    retry = 0

                    if from_token == 'eth':
                        wait_balance(pk, chain, old_balance + 0.000001, to_token_address)
                        sleeping(15, 60)
                        if make_pool == True:
                            velocore_bridge(pk, token_to_pool_from, token_to_pool_to)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break


            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    return

def izumi_swap(pk, retry=0):

    amount_from, amount_to, amount_token_from, amount_token_to, tokens, slippage = value_izumi()

    chain = 'zksync'
    web3 = get_web3(chain)
    wallet = web3.eth.account.from_key(pk).address

    token = random.choice(tokens)
    _, token_decimals, _ = check_data_token(web3, ZKSYNC_TOKENS_CONTACT[token])

    swap_refund_contract = web3.eth.contract(address=web3.to_checksum_address("0x943ac2310D9BC703d6AB5e5e76876e212100f894"), abi=IZUMI_ABI) # `SWAP` contract from docs
    pool_contract = web3.eth.contract(address=web3.to_checksum_address("0x43ff8a10B6678462265b00286796e88f03C8839A"), abi=IZUMI_POOL_ABI) # ETH-USDC pool

    amount = round(random.uniform(amount_from, amount_to), 7)
    amount_back = random.uniform(amount_token_from, amount_token_to)
    contract_fee = 2000 # 0.2%

    for from_token, to_token in zip(['eth', token], [token, 'eth']):
        while True:
            try:
                module_str = f'izumi swap {from_token} -> {to_token}'
                logger.info(module_str)

                current_points = pool_contract.functions.state().call()[1]
                price = (1.0001 ** current_points) / 10 ** (18 - token_decimals)

                token_balance = check_balance(pk, chain, ZKSYNC_TOKENS_CONTACT[token])
                if from_token == 'eth':
                    to_send = tx_value = int(amount * 10 ** 18)
                    to_receive = int(amount / price * 10 ** token_decimals * 0.998) # `* 0.998` for more correctly price
                else:
                    to_send = int(token_balance * amount_back * 10 ** token_decimals)
                    tx_value = 0
                    to_receive = int(token_balance * amount_back * price * 10 ** 18 * 0.998) # `* 0.998` for more correctly price

                    approve_(to_send, pk, chain, ZKSYNC_TOKENS_CONTACT[from_token], swap_refund_contract.address)
                min_to_receive = int((1 - slippage / 100) * to_receive)

                path_connector = f'00' \
                                 f'{hex(contract_fee // 4096 % 16)[2:]}' \
                                 f'{hex(contract_fee // 256 % 16)[2:]}' \
                                 f'{hex(contract_fee // 16 % 16)[2:]}' \
                                 f'{hex(contract_fee % 16)[2:]}'
                path = ZKSYNC_TOKENS_CONTACT[from_token] + path_connector + ZKSYNC_TOKENS_CONTACT[to_token][2:]

                multicall_bytes = []
                if from_token == 'eth':
                    p = (path, wallet, to_send, min_to_receive, int(time.time()) + 300)
                    multicall_bytes.append(swap_refund_contract.functions.swapAmount(p)._encode_transaction_data())
                    multicall_bytes.append(swap_refund_contract.functions.refundETH()._encode_transaction_data())
                else:
                    p = (path, '0x0000000000000000000000000000000000000000', to_send, min_to_receive, int(time.time()) + 300)
                    multicall_bytes.append(swap_refund_contract.functions.swapAmount(p)._encode_transaction_data())
                    multicall_bytes.append(swap_refund_contract.functions.unwrapWETH9(0, wallet)._encode_transaction_data())

                contract_txn = swap_refund_contract.functions.multicall(multicall_bytes).build_transaction({
                            'value': tx_value,
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gasPrice': web3.eth.gas_price,
                        })

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(contract_txn['gas'] * contract_txn['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, contract_txn, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'izumi {from_token}-{to_token}')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')
                    retry = 0

                    if from_token == 'eth':
                        wait_balance(pk, chain, token_balance + 0.000001, ZKSYNC_TOKENS_CONTACT[to_token])
                        sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    return

def unpool(pk):

    def unpool_syncswap(retry=0):

        slippage = 0.4 # 0.4%

        for token in list(SYNCSWAP_POOLS.keys()):
            while True:
                try:
                    module_str = f'unpool from syncswap'

                    lp_contract = web3.eth.contract(address=web3.to_checksum_address(SYNCSWAP_POOLS[token]), abi=ABI_POOL_SYNCSWAP)
                    syncswap_pool_contract = web3.eth.contract(address=web3.to_checksum_address('0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295'), abi=ABI_SWAP_SYNCSWAP)

                    lp_balance = lp_contract.functions.balanceOf(wallet).call()
                    if lp_balance > 0:
                        module_str = f'unpool from syncswap eth-{token}'
                        logger.info(module_str)

                        approve_(lp_balance, pk, chain, lp_contract.address, syncswap_pool_contract.address)

                        data = abi.encode(
                            ['address', 'address', 'uint256'],
                            [ZKSYNC_TOKENS_CONTACT['eth'], wallet, 1]
                        )

                        reserves = lp_contract.functions.getReserves().call() # response: [token_res, eth_res]
                        total_supply = lp_contract.functions.totalSupply().call()

                        amount_eth_min = int(lp_balance * reserves[1] / total_supply * 2 * (1 - slippage/100))

                        tx = syncswap_pool_contract.functions.burnLiquiditySingle(
                            lp_contract.address,                            # pool
                            lp_balance,                                     # liquidity
                            data,                                           # data
                            amount_eth_min,                                 # minAmount
                            '0x0000000000000000000000000000000000000000',   # callback
                            '0x'                                            # callbackData
                        ).build_transaction({
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gasPrice': web3.eth.gas_price,
                        })

                        # смотрим газ, если выше выставленного значения : спим
                        total_fee = int(tx['gas'] * tx['gasPrice'])
                        is_fee = checker_total_fee(chain, total_fee)
                        if is_fee == False: continue

                        tx_hash = sign_tx(web3, tx, pk)
                        tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                        status = check_status_tx(chain, tx_hash, f'unpool syncswap eth-{token}')

                        if status == 1:
                            logger.success(f'{module_str} | {tx_link}')
                            list_send.append(f'{STR_DONE}{module_str}')

                            retry = 0
                            sleeping(15, 60)
                            break

                        else:
                            logger.error(f'{module_str} | tx is failed | {tx_link}')
                            if retry < RETRY:
                                retry += 1
                                continue
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                                break

                    else: break

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return

    def unpool_muteswap(retry=0):
        slippage = 0.2 # 0.2%

        for token in list(MUTESWAP_POOLS.keys()):
            while True:
                try:
                    module_str = 'unpool from muteswap'

                    lp_contract = web3.eth.contract(address=web3.to_checksum_address(MUTESWAP_POOLS[token]), abi=ABI_MUTESWAP_LP)
                    muteswap_pool_contract = web3.eth.contract(address=web3.to_checksum_address('0x8b791913eb07c32779a16750e3868aa8495f5964'), abi=ABI_SWAP_MUTE)

                    lp_balance = lp_contract.functions.balanceOf(wallet).call()
                    if lp_balance > 0:
                        module_str = f'unpool from muteswap eth-{token}'
                        logger.info(module_str)

                        approve_(lp_balance, pk, chain, lp_contract.address, muteswap_pool_contract.address)

                        reserves = lp_contract.functions.getReserves().call() # response: [token_res, eth_res, timestamp]
                        total_supply = lp_contract.functions.totalSupply().call()

                        amount_token_min = int(lp_balance * reserves[0] / total_supply * (1 - slippage/100))
                        amount_eth_min = int(lp_balance * reserves[1] / total_supply * (1 - slippage/100))

                        tx = muteswap_pool_contract.functions.removeLiquidityETHSupportingFeeOnTransferTokens(
                            web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token]), # pool token
                            lp_balance,                                             # liquidity
                            amount_token_min,                                       # amountTokenMin
                            amount_eth_min,                                         # amountETHMin
                            wallet,                                                 # to
                            int(time.time()) + 300,                                 # deadline
                            False,                                                  # stable
                        ).build_transaction({
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gasPrice': web3.eth.gas_price,
                        })

                        # смотрим газ, если выше выставленного значения : спим
                        total_fee = int(tx['gas'] * tx['gasPrice'])
                        is_fee = checker_total_fee(chain, total_fee)
                        if is_fee == False: continue

                        tx_hash = sign_tx(web3, tx, pk)
                        tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                        status = check_status_tx(chain, tx_hash, f'unpool muteswap eth-{token}')

                        if status == 1:
                            logger.success(f'{module_str} | {tx_link}')
                            list_send.append(f'{STR_DONE}{module_str}')

                            retry = 0
                            sleeping(15, 60)

                            mute_swap(pk, forced_token=token)

                            break

                        else:
                            logger.error(f'{module_str} | tx is failed | {tx_link}')
                            if retry < RETRY:
                                retry += 1
                                continue
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                                break

                    else: break

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return

    def unpool_spacefi(retry=0):
        slippage = 0.2 # 0.2%

        for token in list(SPACEFI_POOLS.keys()):
            while True:
                try:
                    module_str = 'unpool from spacefi'

                    lp_contract = web3.eth.contract(address=web3.to_checksum_address(SPACEFI_POOLS[token]), abi=ABI_MUTESWAP_LP)
                    spacefi_pool_contract = web3.eth.contract(address=web3.to_checksum_address('0xbe7d1fd1f6748bbdefc4fbacafbb11c6fc506d1d'), abi=SPACE_ABI)

                    lp_balance = lp_contract.functions.balanceOf(wallet).call()
                    if lp_balance > 0:
                        module_str = f'unpool from spacefi eth-{token}'
                        logger.info(module_str)

                        approve_(lp_balance, pk, chain, lp_contract.address, spacefi_pool_contract.address)

                        reserves = lp_contract.functions.getReserves().call() # response: [token_res, eth_res, timestamp]
                        total_supply = lp_contract.functions.totalSupply().call()

                        amount_token_min = int(lp_balance * reserves[0] / total_supply * (1 - slippage/100))
                        amount_eth_min = int(lp_balance * reserves[1] / total_supply * (1 - slippage/100))

                        tx = spacefi_pool_contract.functions.removeLiquidityETH(
                            web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token]), # pool token
                            lp_balance,                                             # liquidity
                            amount_token_min,                                       # amountTokenMin
                            amount_eth_min,                                         # amountETHMin
                            wallet,                                                 # to
                            int(time.time()) + 300,                                 # deadline
                        ).build_transaction({
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gasPrice': web3.eth.gas_price,
                        })

                        # смотрим газ, если выше выставленного значения : спим
                        total_fee = int(tx['gas'] * tx['gasPrice'])
                        is_fee = checker_total_fee(chain, total_fee)
                        if is_fee == False: continue

                        tx_hash = sign_tx(web3, tx, pk)
                        tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                        status = check_status_tx(chain, tx_hash, f'unpool spacefi eth-{token}')

                        if status == 1:
                            logger.success(f'{module_str} | {tx_link}')
                            list_send.append(f'{STR_DONE}{module_str}')

                            retry = 0
                            sleeping(15, 60)

                            mute_swap(pk, forced_token=token)

                            break

                        else:
                            logger.error(f'{module_str} | tx is failed | {tx_link}')
                            if retry < RETRY:
                                retry += 1
                                continue
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                                break

                    else: break

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return

    def unpool_velocore(retry=0):
        slippage = 0.2 # 0.2%

        for token in list(VELOCORE_POOLS.keys()):
            while True:
                try:
                    module_str = 'unpool from velocore'

                    lp_token = web3.eth.contract(address=web3.to_checksum_address(VELOCORE_POOLS[token]), abi=VELOCORE_PAIR_ABI)
                    velocore_pool_contract = web3.eth.contract(address=web3.to_checksum_address('0xcd52cbc975fbb802f82a1f92112b1250b5a997df'), abi=VELOCORE_PAIR_ABI)
                    liquidity_manager = web3.eth.contract(address=web3.to_checksum_address('0xd999e16e68476bc749a28fc14a0c3b6d7073f50c'), abi=VELOCORE_ABI)

                    lp_balance = lp_token.functions.balanceOf(wallet).call()
                    unstaked_balance = velocore_pool_contract.functions.balanceOf(wallet).call()

                    if lp_balance > 0:
                        module_str = f'unstake from velocore eth-{token}'
                        logger.info(module_str)

                        approve_(lp_balance, pk, chain, velocore_pool_contract.address, liquidity_manager.address)

                        tx = lp_token.functions.withdraw(lp_balance).build_transaction({
                            'from': wallet,
                            'nonce': web3.eth.get_transaction_count(wallet),
                            'gasPrice': web3.eth.gas_price,
                        })

                        # смотрим газ, если выше выставленного значения : спим
                        total_fee = int(tx['gas'] * tx['gasPrice'])
                        is_fee = checker_total_fee(chain, total_fee)
                        if is_fee == False: continue

                        tx_hash = sign_tx(web3, tx, pk)
                        tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                        status = check_status_tx(chain, tx_hash, f'unstake velocore eth-{token}')

                        if status == 1:
                            logger.success(f'{module_str} | {tx_link}')
                            list_send.append(f'{STR_DONE}{module_str}')

                            retry = 0
                            sleeping(15, 60)
                            continue
                        else:
                            logger.error(f'{module_str} | tx is failed | {tx_link}')
                            if retry < RETRY:
                                retry += 1
                                continue
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                                break

                    elif unstaked_balance > 0:
                        module_str = f'withdraw from velocore eth-{token}'
                        logger.info(module_str)

                        reserves = velocore_pool_contract.functions.getReserves().call() # response: [token_res, eth_res, timestamp]
                        total_supply = velocore_pool_contract.functions.totalSupply().call()

                        amount_token_min = int(unstaked_balance * reserves[0] / total_supply * (1 - slippage/100))
                        amount_eth_min = int(unstaked_balance * reserves[1] / total_supply * (1 - slippage/100))


                        tx = liquidity_manager.functions.removeLiquidityETH(
                            web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT[token]),
                            False,
                            unstaked_balance,
                            amount_token_min,
                            amount_eth_min,
                            wallet,
                            int(time.time()) + 300,
                        )

                        # смотрим газ, если выше выставленного значения : спим
                        total_fee = int(tx['gas'] * tx['gasPrice'])
                        is_fee = checker_total_fee(chain, total_fee)
                        if is_fee == False: continue

                        tx_hash = sign_tx(web3, tx, pk)
                        tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                        status = check_status_tx(chain, tx_hash, f'withdraw velocore eth-{token}')

                        if status == 1:
                            logger.success(f'{module_str} | {tx_link}')
                            list_send.append(f'{STR_DONE}{module_str}')
                            sleeping(15, 60)

                            mute_swap(pk, forced_token=token)
                            break
                        else:
                            logger.error(f'{module_str} | tx is failed | {tx_link}')
                            if retry < RETRY:
                                retry += 1
                                continue
                            else:
                                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                                break
                    else: break

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return


    chain = 'zksync'
    web3 = get_web3(chain)
    wallet = web3.eth.account.from_key(pk).address

    unpool_syncswap()
    unpool_muteswap()
    #unpool_spacefi()
    #unpool_velocore()

def odos(pk):
        def get_tx(tokenA, tokenB, amount, max_difference, retry=0):
            while True:
                try:
                    proxy_data = get_proxy()
                    if proxy_data:
                        if proxy_data['type'] == 'default':
                            logger.debug(f'using {proxy_data["proxy"]}')
                        proxies = {
                            'http': proxy_data["proxy"],
                            'https': proxy_data["proxy"],
                        }

                    tokenA_address = ZKSYNC_TOKENS_CONTACT[tokenA]
                    tokenB_address = ZKSYNC_TOKENS_CONTACT[tokenB]
                    # Sources: "eZKalibur Stable","eZKalibur Volatile","GemSwap","iZiSwap","Maverick","Mute.io Stable","Mute.io Volatile","Overnight Exchange","PancakeSwap","PancakeSwap V3","Solunea Stable","Solunea Volatile","SpaceFi","SyncSwap Classic","SyncSwap Stable","Velocore Stable","Velocore Volatile","veSync Stable","veSync Volatile","WOOFi V2","Wrapped Ether","zkSwap Finance"
                    if tokenA == 'eth' or tokenB == 'eth':
                        sourceWhitelist = []
                    else:
                        sourceWhitelist = ['Velocore Stable', 'Maverick']

                    if tokenA_address == '0x5aea5775959fbc2557cc8789bc1bf90a239d9a91': tokenA_address = '0x0000000000000000000000000000000000000000'
                    elif tokenB_address == '0x5aea5775959fbc2557cc8789bc1bf90a239d9a91': tokenB_address = '0x0000000000000000000000000000000000000000'
                    payload = {
                        "chainId": 324,
                        "inputTokens": [
                            {
                                "tokenAddress": web3.to_checksum_address(tokenA_address),
                                "amount": str(amount)
                            }
                        ],
                        "outputTokens": [
                            {
                                "tokenAddress": web3.to_checksum_address(tokenB_address),
                                "proportion": 1
                            }
                        ],
                        "gasPrice": 0.25,
                        "userAddr": wallet,
                        "slippageLimitPercent": 0.3,
                        'pathViz': True,
                        "sourceWhitelist": sourceWhitelist,
                    }

                    if proxy_data: r = requests.post('https://api.odos.xyz/sor/quote/v2', json=payload, proxies=proxies)
                    else: r = requests.post('https://api.odos.xyz/sor/quote/v2', json=payload)

                    path_id = r.json()['pathId']
                    if tokenA != 'eth' and tokenB != 'eth':
                        value_in = r.json()['pathViz']['links'][0]['in_value']
                        value_out = r.json()['pathViz']['links'][0]['out_value']
                        if value_in - value_out > max_difference:
                            logger.warning(f'odos swap {tokenA} -> {tokenB} cost too much! {value_in-value_out}$ > {max_difference}$')
                            return 'Cost too much'

                    payload = {
                        "userAddr": wallet,
                        "pathId": path_id,
                        "simulate": True
                    }
                    if proxy_data: r2 = requests.post('https://api.odos.xyz/sor/assemble', json=payload, proxies=proxies)
                    else: r2 = requests.post('https://api.odos.xyz/sor/assemble', json=payload)

                    if not r2.json()['simulation']['isSuccess']:
                        logger.error(f'odos simalate failed: {r2.json()["simulation"]["simulationError"]["errorMessage"]}')
                        time.sleep(10)

                    return r2.json()['transaction']

                except Exception as error:
                    logger.error(f'odos get quotes error | {error}\n{r2.text}')
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}odos get quotes error')
                        return False

        def odos_swap(from_eth=False, between_stables=False, to_eth=False, retry=0):
            swap_from, swap_to, max_difference = value_odos()
            pool = ['usdc', 'busd']

            if from_eth:
                from_token = 'eth'
                to_token = random.choice(pool)
            elif between_stables:
                from_token = between_stables
                pool.remove(from_token)
                to_token = random.choice(pool)
            elif to_eth:
                if to_eth == 'Failed': from_token = get_the_most_balance(pk)
                else: from_token = to_eth
                to_token = 'eth'
            else: return False

            while True:
                try:
                    module_str = f'odos swap {from_token} -> {to_token}'
                    logger.info(module_str)

                    if from_token == 'eth':
                        amount = int(check_balance(pk, chain, human=False) * random.uniform(swap_from, swap_to))
                    else:
                        amount = check_balance(pk, chain, ZKSYNC_TOKENS_CONTACT[from_token], human=False)

                    approve_(amount, pk, chain, ZKSYNC_TOKENS_CONTACT[from_token], '0xa269031037b4d5fa3f771c401d19e57def6cb491')
                    old_balance = check_balance(pk, chain, ZKSYNC_TOKENS_CONTACT[to_token])

                    tx_data = get_tx(from_token, to_token, amount, max_difference)
                    if not tx_data: return False
                    elif tx_data == 'Cost too much':
                        sleeping(20,20)
                        return odos_swap(from_eth, between_stables, to_eth, retry)

                    approve_(amount, pk, chain, ZKSYNC_TOKENS_CONTACT[from_token], tx_data['to'])

                    tx = {
                        'chainId': web3.eth.chain_id,
                        'from': wallet,
                        'nonce': web3.eth.get_transaction_count(wallet),
                        'gasPrice': web3.eth.gas_price,
                        'to': tx_data['to'],
                        'value': int(tx_data['value']),
                        'data': tx_data['data'],
                    }
                    tx['gas'] = web3.eth.estimate_gas(tx)

                    # смотрим газ, если выше выставленного значения : спим
                    total_fee = int(tx['gas'] * tx['gasPrice'])
                    is_fee = checker_total_fee(chain, total_fee)
                    if is_fee == False: continue

                    tx_hash = sign_tx(web3, tx, pk)
                    tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                    status = check_status_tx(chain, tx_hash, f'odos swap')

                    if status == 1:
                        logger.success(f'{module_str} | {tx_link}')
                        list_send.append(f'{STR_DONE}{module_str}')

                        if to_token != 'eth':
                            wait_balance(pk, chain, old_balance + 0.000001, ZKSYNC_TOKENS_CONTACT[to_token])
                        sleeping(15, 60)
                        return to_token

                    else:
                        logger.error(f'{module_str} | tx is failed | {tx_link}')
                        if retry < RETRY:
                            retry += 1
                            continue
                        else:
                            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                            return 'Failed'

                except Exception as error:
                    logger.error(f'{module_str} | {error}')
                    try: logger.debug(f'tx_data: {tx_data}')
                    except: pass
                    if retry < RETRY:
                        retry += 1
                        sleeping(10, 20)
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str}')
                        return 'Failed'

        chain = 'zksync'
        web3 = get_web3(chain)
        wallet = web3.eth.account.from_key(pk).address

        last_token = odos_swap(from_eth=True)
        if last_token != 'Failed':
            for _ in range(random.randint(TRANSACTIONS_COUNT['odos'][0], TRANSACTIONS_COUNT['odos'][1])):
                last_token = odos_swap(between_stables=last_token)
                if last_token == 'Failed': break
            odos_swap(to_eth=last_token)

def dmail(pk, retry=0):
    try:
        from_chain = 'zksync'

        web3 = get_web3(from_chain, pk)
        send_to = web3.eth.account.create().address

        module_str = f'dmail to {send_to}'
        logger.info(module_str)

        wallet = web3.eth.account.from_key(pk).address

        contract = web3.eth.contract(address=web3.to_checksum_address('0x981F198286E40F9979274E0876636E9144B8FB8E'), abi=ZK_DMAIL_ABI)

        to = sha256((wallet.lower()+'@dmail.ai').encode()).hexdigest() # my address
        subject = sha256((send_to.lower()+'@dmail.ai').encode()).hexdigest() # random address

        contract_tx = contract.functions.send_mail(to, subject).build_transaction({
            "chainId": web3.eth.chain_id,
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'gasPrice': web3.eth.gas_price,
        })

        # смотрим газ, если выше выставленного значения : спим
        total_fee   = int(contract_tx['gas'] * contract_tx['gasPrice'])
        is_fee      = checker_total_fee(from_chain, total_fee)

        if is_fee == True:

            tx_hash = sign_tx(web3, contract_tx, pk)
            tx_link = f'{DATA[from_chain]["scan"]}/{tx_hash}'

            status = check_status_tx(from_chain, tx_hash, 'send dmail')
            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    dmail(pk, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

        else:
            dmail(pk)

    except Exception as error:
        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            logger.info(f'try again | {wallet}')
            sleeping(10, 10)
            dmail(pk, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def across(pk, retry=0):
    def get_relay_fee(amount, retry=0):
        while True:
            try:
                proxy_data = get_proxy()
                if proxy_data:
                    if proxy_data['type'] == 'default':
                        logger.debug(f'using {proxy_data["proxy"]}')
                    proxies = {
                        'http': proxy_data["proxy"],
                        'https': proxy_data["proxy"],
                    }

                url = 'https://across.to/api/suggested-fees?token=0x5aea5775959fbc2557cc8789bc1bf90a239d9a91&destinationChainId=42161&amount=1000000000000000000'
                if proxy_data:
                    r = requests.get(url, proxies=proxies)
                else:
                    r = requests.post(url)
                relay_fee = int(r.json()['relayFeePct']) # ~0.0005 * 10 ** 18
                fee_in_eth = relay_fee / 10 ** 18 * amount
                if fee_in_eth > 0.0021: # 0.0021 ETH ~3.5$
                    logger.warning(f'across too big fee: {round(fee_in_eth, 6)} ETH with value {amount} ETH')
                    time.sleep(15)
                return relay_fee, r.json()['timestamp']

            except Exception as error:
                logger.error(f'across get fee error | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}across get fee error')
                    return False

    try:
        from_chain = 'zksync'
        web3 = get_web3(from_chain, pk)

        keep_from, keep_to = value_across()
        balance = check_balance(pk, from_chain)
        keep = round(random.uniform(keep_from, keep_to), 8)
        amount = round(balance - keep - 0.0003, 5)

        module_str = f'across {from_chain} to arbitrum {amount} ETH'
        logger.info(module_str)

        wallet = web3.eth.account.from_key(pk).address

        contract = web3.eth.contract(address=web3.to_checksum_address('0xE0B015E54d54fc84a6cB9B666099c46adE9335FF'), abi=ACROSS_ABI)
        relay_fee, timestamp = get_relay_fee(amount)
        if not relay_fee: return False

        contract_tx = contract.functions.deposit(
            wallet,
            web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT['eth']),
            int(amount * 10 ** 18),
            42161, # to arb
            relay_fee, # relayerFeePct
            int(timestamp), # int(time.time() / 100) * 100,
            "0x",
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).build_transaction({
            "chainId": web3.eth.chain_id,
            'from': wallet,
            'nonce': web3.eth.get_transaction_count(wallet),
            'gasPrice': web3.eth.gas_price,
            'value': int(amount * 10 ** 18)
        })

        # смотрим газ, если выше выставленного значения : спим
        total_fee   = int(contract_tx['gas'] * contract_tx['gasPrice'])
        is_fee      = checker_total_fee(from_chain, total_fee)

        if is_fee == True:

            tx_hash = sign_tx(web3, contract_tx, pk)
            tx_link = f'{DATA[from_chain]["scan"]}/{tx_hash}'

            status = check_status_tx(from_chain, tx_hash, 'across to zk era -> arbitrum')
            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    across(pk, retry+1)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
        else:
            across(pk)

    except Exception as error:
        logger.error(f'{module_str} | {error}')
        if retry < RETRY:
            logger.info(f'try again | {wallet}')
            sleeping(10, 10)
            across(pk, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def eralend(pk):

    def eralend_repay(retry=0):
        """
        withdraw liquidity from eralend
        """

        while True:
            try:

                module_str = 'repay USDC for eralend'
                usdc_contract = web3.eth.contract(address=web3.to_checksum_address(ZKSYNC_TOKENS_CONTACT['usdc']),
                                                  abi=ERC20_ABI)
                usdc_balance = usdc_contract.functions.balanceOf(wallet).call()

                value_to_repay = usdc_eralend_contract.functions.borrowBalanceStored(wallet).call()
                # value_to_repay = usdc_eralend_contract.functions.borrowBalanceCurrent(wallet).call()
                amount_to_repay = value_to_repay / 10 ** 6
                module_str = f'repay {round(amount_to_repay, 6)} USDC for eralend'

                if value_to_repay > usdc_balance:
                    amount_difference = (value_to_repay - usdc_balance) / 10 ** 6
                    logger.error(
                        f'cant {module_str} because USDC balance now is {usdc_balance / 10 ** 6} (difference {amount_difference} USDC)')

                    if amount_difference < 10:
                        logger.info(f'Trying to swap ETH to {amount_difference} USDC')
                        space_swap(pk, needed_usdc=value_to_repay - usdc_balance)
                        continue

                    else:
                        text = f'CANT REPAY USDC TO ERALEND!!! NEED {amount_difference} USDC MORE!!!'
                        for i in range(3):
                            logger.error(text)
                            send_msg(text=f'[{wallet}]\n💥{text}')
                        logger.debug(f'Press Enter when USDC balance will be at least {value_to_repay / 10 ** 6}')
                        input()
                        continue

                approve_(value_to_repay, pk, chain, usdc_contract.address, usdc_eralend_contract.address)

                tx = usdc_eralend_contract.functions.repayBorrow(value_to_repay).build_transaction({
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(tx['gas'] * tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'repay USDC for eralend')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')

                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    break

    def eralend_withdraw(retry=0):
        """
        withdraw liquidity from eralend
        """

        multiplier = 1
        while True:
            module_str = 'withdraw from eralend'
            try:

                # decimals = eth_eralend_contract.functions.decimals().call() # = 8
                # _, balance, _, rate = eth_eralend_contract.functions.getAccountSnapshot(wallet).call()
                # amount = (balance / 10 ** decimals) * (rate / 10 ** (18 + 18 - decimals))
                # same
                value = int(eth_eralend_contract.functions.balanceOfUnderlying(wallet).call() * multiplier)
                amount = value / 10 ** 18

                module_str = f'withdraw from eralend {round(amount, 6)} ETH'


                tx = eth_eralend_contract.functions.redeemUnderlying(value).build_transaction({
                    'from': wallet,
                    'value': 0,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(tx['gas'] * tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'withdraw from eralend')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')

                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 0.5
                    multiplier -= 0.001
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    break

    def approve_eth_on_eralend(retry=0):
        "Use as Collateral"

        module_str = 'approve eth on eralend'
        while True:
            try:
                tx = {
                    'chainId': web3.eth.chain_id,
                    'from': wallet,
                    # 'to': web3.to_checksum_address('0x0171cA5b372eb510245F5FA214F5582911934b3D'),
                    # 'data': '0xc2998238000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000001bbd33384869b30a323e15868ce46013c82b86fb',
                    'to': web3.to_checksum_address('0xC955d5fa053d88E7338317cc6589635cD5B2cf09'),
                    'data': '0xc29982380000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000100000000000000000000000022d8b71599e14f20a49a397b88c1c878c86f5579',
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                    'value': 0
                }
                tx['gas'] = web3.eth.estimate_gas(tx)

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(tx['gas'] * tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, module_str)

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')

                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        raise ValueError

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    raise ValueError(f'Cant Approve Eth on Eralend')

    def eralend_supply(retry=0):
        "supply liquidity for eralend"

        min_amount_eth, max_amount_eth, min_percent_eth, max_percent_eth, min_borrow, max_borrow = value_eralend()

        while True:
            try:
                if min_amount_eth != 0:
                    amount = random.uniform(min_amount_eth, max_amount_eth)
                else:
                    all_balance = check_balance(pk, chain)
                    amount = all_balance * random.uniform(min_percent_eth, max_percent_eth) / 100
                value = int(amount * 10 ** 18)

                module_str = f'supply for eralend {round(amount, 6)} ETH'

                tx = eth_eralend_contract.functions.mint().build_transaction({
                    'from': wallet,
                    'value': value,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(tx['gas'] * tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'supply for eralend')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')

                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    break

    def eralend_borrow(retry=0):
        """
        borrow usdc for eth on eralend
        """

        min_amount_eth, max_amount_eth, min_percent_eth, max_percent_eth, min_borrow, max_borrow = value_eralend()

        while True:
            try:
                eth_price = get_native_prices()
                eth_in_liquidity = eth_eralend_contract.functions.balanceOfUnderlying(wallet).call() / 10 ** 18
                amount_supplied = eth_in_liquidity * eth_price  # total liquidity in ETH Pool. calculate in $ because we will borrow USDC
                borrow_limit = amount_supplied * 0.725  # Loan-To-Value = 72.5%
                amount_to_borrow = borrow_limit * random.randint(min_borrow, max_borrow) / 100
                value_to_borrow = int(amount_to_borrow * 10 ** 6)

                module_str = f'borrow {round(amount_to_borrow, 3)} USDC on eralend'

                tx = usdc_eralend_contract.functions.borrow(value_to_borrow).build_transaction({
                    'from': wallet,
                    'nonce': web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                })

                # смотрим газ, если выше выставленного значения : спим
                total_fee = int(tx['gas'] * tx['gasPrice'])
                is_fee = checker_total_fee(chain, total_fee)
                if is_fee == False: continue

                tx_hash = sign_tx(web3, tx, pk)
                tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

                status = check_status_tx(chain, tx_hash, f'borrow USDC')

                if status == 1:
                    logger.success(f'{module_str} | {tx_link}')
                    list_send.append(f'{STR_DONE}{module_str}')

                    sleeping(15, 60)
                    break

                else:
                    logger.error(f'{module_str} | tx is failed | {tx_link}')
                    if retry < RETRY:
                        retry += 1
                        continue
                    else:
                        list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                        break

            except Exception as error:
                logger.error(f'{module_str} | {error}')
                if retry < RETRY:
                    retry += 1
                    sleeping(10, 20)
                else:
                    list_send.append(f'{STR_CANCEL}{module_str}')
                    break


    chain = 'zksync'
    web3 = get_web3(chain, pk)
    wallet = web3.eth.account.from_key(pk).address

    # eth_eralend_contract = web3.eth.contract(web3.to_checksum_address('0x1BbD33384869b30A323e15868Ce46013C82B86FB'), abi=ERALEND_ABI)
    # usdc_eralend_contract = web3.eth.contract(web3.to_checksum_address('0x1181D7BE04D80A8aE096641Ee1A87f7D557c6aeb'), abi=ERALEND_ABI)
    eth_eralend_contract = web3.eth.contract(web3.to_checksum_address('0x22D8b71599e14F20a49a397b88c1C878c86F5579'), abi=ERALEND_ABI)
    usdc_eralend_contract = web3.eth.contract(web3.to_checksum_address('0x90973213E2a230227BD7CCAfB30391F4a52439ee'), abi=ERALEND_ABI)

    eralend_supply()
    approve_eth_on_eralend()
    eralend_borrow()
    eralend_repay()
    eralend_withdraw()


# ============== zkSync Lite ==============

def zk_lite_transfer(pk, to, amount, breakk=False):
    module_str = f'zk lite transfer {amount} ETH -> {to}'
    logger.info(f'{module_str} ({breakk})')

    async def run():

        library = ZkSyncLibrary()
        provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))

        account = Account.from_key(pk)
        ethereum_signer = EthereumSignerWeb3(account=account)
        contracts = await provider.get_contract_address()

        w3 = get_web3("ethereum", pk)
        zksync = ZkSync(account=account, web3=w3,
                        zksync_contract_address=contracts.main_contract)
        ethereum_provider = EthereumProvider(w3, zksync)

        signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
        wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer, eth_signer=ethereum_signer, provider=provider)

        if not await wallet.is_signing_key_set():
            tx = await wallet.set_signing_key("ETH", eth_auth_data=ChangePubKeyEcdsa())
            status = await tx.await_committed()
            logger.info(f'unlock zksync lite account status: {status.status.name}')
            sleeping(10,20)

        tx = await wallet.transfer(w3.to_checksum_address(to), amount=Decimal(str(amount)), token="ETH")
        tx_link = f'https://zkscan.io/explorer/transactions/{tx.transaction_hash.split(":")[1]}'
        logger.info(f'zksync lite : transfer - 0x{tx.transaction_hash.split(":")[1]}')

        status = await tx.await_committed()

        if status.status.name == 'COMMITTED':
            logger.success(f'{module_str} | {tx_link}')
            list_send.append(f'{STR_DONE}{module_str}')
            sleeping(20, 40)
        else:
            logger.error(f'{module_str} | tx is failed ({status.fail_reason}) | {tx_link}')
            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed ({status.fail_reason}) | <a href="{tx_link}">link 👈</a>')
            sleeping(5, 20)

    try:
        asyncio.run(run())
    except Exception as err:
        logger.error(f'zklite transfer error: {err}')
        if not breakk:
            if len(str(amount)) == 14:
                new_amount = str(amount)[:9] + str(amount)[-4:]
                zk_lite_transfer(pk, to, new_amount, True)

def zk_lite_to_okx(pk):
    to = RECIPIENTS_WALLETS[pk]
    balance = zk_lite_check_balance(pk)
    keep_from, keep_to = value_keep_transfer()
    keep = random.uniform(keep_from, keep_to)

    zk_lite_transfer(pk, to, round(balance - keep, 6))

def zk_lite_check_balance(pk):
    async def run():
        library = ZkSyncLibrary()
        provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))

        account = Account.from_key(pk)
        ethereum_signer = EthereumSignerWeb3(account=account)
        contracts = await provider.get_contract_address()

        w3 = get_web3("zksync", pk)
        zksync = ZkSync(account=account, web3=w3,
                        zksync_contract_address=contracts.main_contract)
        ethereum_provider = EthereumProvider(w3, zksync)

        signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
        wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer, eth_signer=ethereum_signer,
                        provider=provider)

        committedETHBalance = await wallet.get_balance("ETH", "committed")
        return committedETHBalance / 10 ** 18

    return asyncio.run(run())

def zk_lite_wait_balance(pk, amount):

    logger.debug(f'wait {round(Decimal(amount), 8)} ETH in zksync lite')

    while True:
        try:
            human_balance = zk_lite_check_balance(pk)
            if human_balance >= amount:
                logger.info(f'balance : {human_balance}')
                break
        except Exception as err: logger.warning(f'zksync lite wait balance error: {err}')
        time.sleep(10)

def zk_lite_mint_nft(pk, retry=0):
    module_str = 'zk lite nft mint'
    logger.info(module_str)

    async def run():
        library = ZkSyncLibrary()
        provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))

        account = Account.from_key(pk)
        ethereum_signer = EthereumSignerWeb3(account=account)
        contracts = await provider.get_contract_address()

        w3 = get_web3("zksync", pk)
        zksync = ZkSync(account=account, web3=w3,
                        zksync_contract_address=contracts.main_contract)
        ethereum_provider = EthereumProvider(w3, zksync)

        signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
        wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer, eth_signer=ethereum_signer,
                        provider=provider)



        if not await wallet.is_signing_key_set():
            tx = await wallet.set_signing_key("ETH", eth_auth_data=ChangePubKeyEcdsa())
            status = await tx.await_committed()
            logger.info(f'unlock zksync lite account status: {status.status.name}')
            sleeping(10,20)

        # random empty nft
        # to_hex = ''.join(random.choices(printable, k=random.randint(10, 250)))
        # nft_cid = '0x' + sha256(to_hex.encode()).hexdigest()

        # random parsed nft from saved list
        nft_ipfs = get_random_nft()
        if nft_ipfs == False: return
        decoded_ipfs = b58decode(nft_ipfs)
        nft_cid = '0x' + encode(decoded_ipfs[2:], 'hex').decode()

        tx = await wallet.mint_nft(str(nft_cid), str(account.address), "ETH")
        tx_link = f'https://zkscan.io/explorer/transactions/{tx.transaction_hash.split(":")[1]}'
        logger.info(f'zksync lite : nft mint - 0x{tx.transaction_hash.split(":")[1]}')

        status = await tx.await_committed()
        if status.status.name == 'COMMITTED':
            logger.success(f'{module_str} | {tx_link}')
            list_send.append(f'{STR_DONE}{module_str}')
            sleeping(20,40)
        else:
            if retry < RETRY:
                raise ValueError(f'{module_str} | tx is failed | {tx_link}')
            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

    try:
        asyncio.run(run())
    except Exception as err:
        logger.error(f'{module_str} | {err}')
        if retry < RETRY:
            sleeping(10, 20)
            zk_lite_mint_nft(pk, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}{module_str}')

def zk_lite_swap_tokens(pk):
    module_str = 'zk lite swap tokens'
    logger.info(module_str)

    async def run():
        library = ZkSyncLibrary()
        provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))

        account = Account.from_key(pk)
        ethereum_signer = EthereumSignerWeb3(account=account)
        contracts = await provider.get_contract_address()

        w3 = get_web3("zksync", pk)
        zksync = ZkSync(account=account, web3=w3,
                        zksync_contract_address=contracts.main_contract)
        ethereum_provider = EthereumProvider(w3, zksync)

        signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
        wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer, eth_signer=ethereum_signer,
                        provider=provider)

        tx = await wallet.get_limit_order("ETH", "USDT", Fraction(2100, 1), RatioType.token, Decimal("0.00001"))
        tx_link = f'https://zkscan.io/explorer/transactions/{tx.transaction_hash.split(":")[1]}'
        logger.info(f'zksync lite : token swap - 0x{tx.transaction_hash.split(":")[1]}')

        status = await tx.await_committed()
        if status.status.name == 'COMMITTED':
            logger.success(f'{module_str} | {tx_link}')
            list_send.append(f'{STR_DONE}{module_str}')
        else:
            logger.error(f'{module_str} | tx is failed ({status.fail_reason}) | {tx_link}')
            list_send.append(f'{STR_CANCEL}{module_str} | tx is failed ({status.fail_reason}) | {tx_link}')

    return asyncio.run(run())

