from rpython.jit.codewriter.policy import JitPolicy

from topaz.main import create_entry_point, get_topaz_config_options


def target(driver, args):
    driver.exe_name = "bin/topaz"
    driver.config.set(**get_topaz_config_options())
    return create_entry_point(driver.config), None


def jitpolicy(driver):
    return JitPolicy()


def handle_config(config, translateconfig):
    from rpython.translator.platform import host_factory
    max_stack_size = 11 << 18  # 2.8 Megs
    if host_factory.name == 'msvc':
        host_factory.cflags += ('/DMAX_STACK_SIZE=%d' % max_stack_size,)
        host_factory.cflags += ('/DRPYTHON_LL2CTYPES',)
    elif host_factory.name in ('linux', 'darwin'):
        host_factory.cflags += ('-DMAX_STACK_SIZE=%d' % max_stack_size,)
        host_factory.cflags += ('-DRPYTHON_LL2CTYPES',) # this is hack needed, because compilation failed to find __vmprof_eval_vmprof
    config.translation.suggest(check_str_without_nul=True)
