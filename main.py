from utils import *


if __name__ == "__main__":
    try:
        zero = 0
        update_name(on_welcome=True)
        PATH = pick_path()

        EXCEL_NAME = create_excel(WALLETS)
        logger.debug(f'wallets saved in {EXCEL_NAME}')
        if RANDOM_WALLETS == True: random.shuffle(WALLETS)

        for index in range(len(WALLETS)):
            try:
                key = WALLETS[index]

                modules_done = 0
                zero += 1
                if get_proxy():
                    if get_proxy()['type'] == 'mobile':
                        WALLETS_PROXIES[key] = change_proxy()
                        logger.debug(f'new proxy: {WALLETS_PROXIES[key]}')

                wallet = evm_wallet(key)
                list_send.append(f'{zero}/{len(WALLETS)} : {wallet}\n')
                print(f'\n{zero}/{len(WALLETS)} : {wallet}')

                # ============================ выбор модулей ============================

                # основные модули
                modules = [
                    syncswap_swap,
                    mute_swap,
                    space_swap,
                    bridge_to_eth_from_era,
                    merkly,
                    velocore_swap,
                    izumi_swap,
                    dmail
                ]
                if PATH == '3':
                    modules += [unpool] # take tokens from all pools and swap to ETH
                elif PATH in ['4', '5', '6']:
                    modules += [odos] # volumes in Odos
                elif PATH in ['7']:
                    modules += [eralend] # volumes in Eralend

                # модули для лайта которые будут сделаны в конце
                lite_modules = [
                    zk_lite_mint_nft,
                ]

                if PATH in ['1', '6', '7']:
                    modules = make_modules_path(modules + lite_modules)
                else:
                    modules = make_modules_path(modules)
                    lite_modules = make_modules_path(lite_modules)

                if PATH in ['1', '3', '6', '7']: module_total_len = [len(modules)]
                elif PATH in ['4', '5']: module_total_len = [len(modules+lite_modules)]
                elif PATH == '2': module_total_len = [1]
                update_name(zero, modules_done, module_total_len)


                # ============================ вывод с биржи ============================
                if CHECK_GWEI == True: wait_gas() # смотрим газ, если выше MAX_GWEI, ждем

                if PATH == '4':
                    amount = okx_withdraw(key, "ERC20")
                    try: float(amount)
                    except: continue

                    wait_balance(key, "ethereum", amount*0.99)
                    sleeping(20, 50)

                    # ethereum -> zk era
                    era_balance = check_balance(key, 'zksync')
                    bridge_eth_to_zksync(key)
                    wait_balance(key, "zksync", era_balance + 0.00011)
                    sleeping(20, 40)

                if PATH in ['5', '6', '7']:
                    amount = okx_withdraw(key, "zkSync Era")
                    try: float(amount)
                    except: continue

                    wait_balance(key, "zksync", amount*0.99)
                    sleeping(20, 50)


                # =========================== ворк ворк ворк ===========================

                if PATH == '2':
                    unpool(key)
                    update_name(zero, modules_done, module_total_len)
                    continue

                # запуск модулей
                for module in modules:
                    if CHECK_GWEI == True: wait_gas()  # смотрим газ, если выше MAX_GWEI, ждем
                    module(key)
                    modules_done += 1
                    update_name(zero, modules_done, module_total_len)
                    sleeping(50, 100)
                if PATH == '1': continue
                logger.success('all ERA modules done\n')

                if PATH in ['4', '5', '6', '7']:
                    if PATH not in ['6', '7']:
                        # zk era -> zk lite
                        lite_balance = zk_lite_check_balance(key)
                        orbiter_bridge(key, 'zksync', 'zksync_lite')
                        zk_lite_wait_balance(key, lite_balance + 0.0001)
                        sleeping(20,50)

                        # запуск модулей для лайта
                        for module in lite_modules:
                            if CHECK_GWEI == True: wait_gas()  # смотрим газ, если выше MAX_GWEI, ждем
                            module(key)
                            modules_done += 1
                            update_name(zero, modules_done, module_total_len)
                            sleeping(50, 100)
                        logger.success('all LITE modules done\n')

                    # zk era -> arbitrum
                    arb_balance = check_balance(key, 'arbitrum')

                    # if random.random() > 0.5: across(key)
                    # else: orbiter_bridge(key, 'zksync', 'arbitrum')
                    across(key)

                    wait_balance(key, 'arbitrum', arb_balance+0.0001)
                    sleeping(20,40)

                    # arbitrum -> okx
                    transfer(key, 'arbitrum')

                # ======================================================================
            except KeyboardInterrupt as err:
                text = f'🚷 SKIP on {update_name(zero, modules_done, module_total_len, on_return=True)}'
                logger.warning(text)
                list_send.append(f'{text}')
            except Exception as err:
                error_text = f'Account error: `{err.__class__.__name__}` {err}'
                logger.error(error_text)
                list_send.append(f'\n💥{error_text}')
            finally:
                if TG_BOT_SEND == True:
                    send_msg() # отправляем результат в телеграм
                list_send.clear()
                replace_excel(EXCEL_NAME, key)

                if index != len(WALLETS)-1:
                    sleeping(30, 90)

        print()
        logger.success(f'ALL {len(WALLETS)} WALLETS DONE | RESULTS IN {EXCEL_NAME}')

    except Exception as err:
        if list_send:
            text = f'⚠️ {err}\nSCRIPT STOPPED on {update_name(zero, modules_done, module_total_len, on_return=True)}'
            logger.error(text)
            if TG_BOT_SEND == True:
                send_msg()
                send_msg(text=text)
            list_send.clear()

    time.sleep(0.1)
    input('\npress Enter to exit...\n\t> Enter')

