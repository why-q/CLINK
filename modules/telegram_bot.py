# pip install python-telegram-bot
import logging
import time
from utils.utils import yaml_config, merge_lists, get_current_time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext,
    Updater,
)
from utils.url_process import (
    urls_text_2_list,
    is_valid_url,
    is_accessible_url,
    filter_valid_urls,
    filter_accessible_urls,
    reg_urls,
)
from modules.crawer import get_titles_and_pcs_from_urls, get_titles_from_urls
from modules.llama import get_summaries_by_urls_or_pcs
from modules.sqlite import (
    setup_sqlite,
    insert_datas_to_sqlite,
    get_ids_by_urls_from_sqlite,
    get_id_by_url_from_sqlite,
    get_row_by_id,
)
from modules.chroma import add_datas_to_chroma, search_by_query_from_chroma
from modules.deepl import translate_text_by_deepl
from utils.settings import app_settings


async def tb_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tb_start_text = yaml_config().get_tb_start_text()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=tb_start_text)


async def tb_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tb_help_text = yaml_config().get_tb_help_text()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=tb_help_text)


async def tb_add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 2:
        title = context.args[0]
        content = context.args[1]
        await process_single_note(
            update=update, context=context, title=title, content=content
        )
    elif len(context.args) == 1:
        content = context.args[0]
        await process_single_note(
            update=update, context=context, title=None, content=content
        )
    else:
        wrong_input_format_text = yaml_config().get_wrong_input_format_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=wrong_input_format_text
        )


# TODO
async def test_note(update: Update, context: CallbackContext):
    keyborad = [
        [
            InlineKeyboardButton("No", callback_data="1"),
            InlineKeyboardButton("Yes", callback_data="2"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyborad)
    await update.message.reply_text(
        "Do you want to add a title?", reply_markup=reply_markup
    )


async def test_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")


async def tb_add_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 2:
        # add url + summary
        url = context.args[0]
        summary = context.args[1]
        summary_ = translate_text_by_deepl(summary)
        await process_single_url(
            update=update, context=context, url=url, title=None, summary=summary_
        )
    elif len(context.args) == 3:
        # add url + title + summary
        url = context.args[0]
        title = context.args[1]
        summary = context.args[2]
        summary_ = translate_text_by_deepl(summary)
        await process_single_url(
            update=update, context=context, url=url, title=title, summary=summary_
        )
    else:
        # logging.error("Error occured when using add command: Wrong input format.")
        wrong_input_format_text = yaml_config().get_wrong_input_format_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=wrong_input_format_text
        )


async def tb_urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = urls_text_2_list(update.message.text)
    await process_urls(update=update, context=context, urls=urls)


async def tb_search_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text[len("/searchnote ") :]
    logging.info(f"Query: {query}")

    if query is None:
        tb_no_searching_keyword_text = yaml_config().get_no_searching_keyword_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_no_searching_keyword_text
        )
    else:
        await search_by_query(update=update, context=context, query=query, tag="note")


async def tb_search_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text[len("/searchurl ") :]
    logging.info(f"Query: {query}")

    if query is None:
        tb_no_searching_keyword_text = yaml_config().get_no_searching_keyword_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_no_searching_keyword_text
        )
    else:
        await search_by_query(update=update, context=context, query=query, tag="link")


async def search_by_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, tag: str = "link"
):
    query_ = translate_text_by_deepl(query)

    app_settings.update_search_keyword(query_)
    app_settings.update_search_tag(tag)
    logging.info(f"Setting static keyword to: {app_settings.search_keyword}")
    logging.info(f"Setting static tag to {app_settings.search_tag}")

    tb_searching_text = yaml_config().get_tb_searching_text()
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text=tb_searching_text
    )

    message_id = message.message_id
    search_n_results = yaml_config().get_search_n_results()
    chroma_path = yaml_config().get_chroma_path()
    if tag == "link":
        collection_name = yaml_config().get_chroma_collection_name()
    else:
        collection_name = yaml_config().get_chroma_note_collection_name()

    await search(
        update=update,
        context=context,
        query_texts=[query_],
        message_id=message_id,
        chroma_path=chroma_path,
        collection_name=collection_name,
        n_results=search_n_results,
        tag=tag,
    )


# TODO
async def tb_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1:
        tb_summarizing_text = yaml_config().get_tb_summarizing_text()
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_summarizing_text
        )

        # doing sth...
        time.sleep(3)

        message_id = message.id
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text="Rubick 是一个基于 Electron 的开源工具箱，可免费集成各种插件。它被设计成一个桌面效率工具箱，可以使用以轻量级著称的 npm 轻松安装和卸载插件。Rubick 的插件数据支持 WebDAV 多终端同步，提供跨多个设备的安全数据同步。值得注意的是，Rubick 包含一个独特的系统插件模式，使插件成为工具箱中不可或缺的一部分。其他功能还包括本地应用程序、文件和文件夹的快速启动功能，支持企业级内联网部署，以及多语言支持。",
            message_id=message_id,
        )
    else:
        wrong_input_format_text = yaml_config().get_wrong_input_format_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=wrong_input_format_text
        )


# BUG message is too long
async def tb_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        more_n_results = yaml_config().get_more_n_results()
    else:
        more_n_results = context.args[0]

    try:
        more_n_results = int(more_n_results)
    except ValueError as e:
        logging.error(f"Error occured when wanting more searching results: {e}")

    logging.info(f"SEARCH_KEYWORD: {app_settings.search_keyword}")
    logging.info(f"SEARCH_TAG: {app_settings.search_tag}")

    if app_settings.search_keyword is None:
        tb_use_search_before_more_text = yaml_config().get_use_search_before_more_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_use_search_before_more_text
        )
    else:
        chroma_path = yaml_config().get_chroma_path()
        collection_name = yaml_config().get_chroma_collection_name()

        await search(
            update=update,
            context=context,
            message_id=None,
            query_texts=[app_settings.search_keyword],
            chroma_path=chroma_path,
            collection_name=collection_name,
            n_results=more_n_results,
            tag=app_settings.search_tag,
        )


async def tb_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(error))


async def tb_non_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tb_non_command_text = yaml_config().get_tb_non_command_text()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=tb_non_command_text
    )


async def process_single_note(
    update: Update, context: ContextTypes.DEFAULT_TYPE, title=None, content=None
):
    # send "Processing note..."
    tb_processing_note_text = yaml_config().get_tb_processing_note_text()
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text=tb_processing_note_text
    )
    message_id = message.message_id

    time = get_current_time()
    url = f"note://{time}"
    if title is None:
        title = "Note - " + time
    summary = content
    tag = "note"

    db_path = yaml_config().get_sqlite_path()
    table_name = yaml_config().get_sqlite_table_name()
    chroma_path = yaml_config().get_chroma_path()
    collection_name = yaml_config().get_chroma_note_collection_name()

    await insert_to_databases(
        update=update,
        context=context,
        message_id=message_id,
        db_path=db_path,
        table_name=table_name,
        chroma_path=chroma_path,
        collection_name=collection_name,
        urls=[url],
        titles=[title],
        summaries=[summary],
        tags=[tag],
        times=[time],
        ctag="note",
    )


async def process_single_url(
    update: Update, context: ContextTypes.DEFAULT_TYPE, url, title=None, summary=None
):
    logging.info(f"Processing single url: {url}")
    if is_valid_url(url) and await is_accessible_url(url):
        await process_single_accessible_url(
            update=update, context=context, url=url, title=title, summary=summary
        )
    else:
        _text = f"The {url} is not valid or accessible."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=_text)


async def process_single_accessible_url(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    url: str,
    title=None,
    summary=None,
):
    if title is None:
        titles = await get_titles_from_urls([url])
        title = titles[0]

    url = reg_urls([url])[0]
    db_path, table_name = setup_sqlite()

    id = get_id_by_url_from_sqlite(db_path=db_path, table_name=table_name, url=url)

    # if url existed
    if id is not None:
        tb_no_new_urls_text = yaml_config().get_tb_no_any_new_urls_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=tb_no_new_urls_text,
        )
    else:
        # send "Processing urls..."
        tb_processing_urls_text = yaml_config().get_tb_processing_urls_text()
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_processing_urls_text
        )
        message_id = message.message_id

        tag = "link"
        time = get_current_time()
        chroma_path = yaml_config().get_chroma_path()
        collection_name = yaml_config().get_chroma_collection_name()

        await insert_to_databases(
            update=update,
            context=context,
            message_id=message_id,
            db_path=db_path,
            table_name=table_name,
            chroma_path=chroma_path,
            collection_name=collection_name,
            urls=[url],
            titles=[title],
            summaries=[summary],
            tags=[tag],
            times=[time],
        )


async def process_urls(update: Update, context: ContextTypes.DEFAULT_TYPE, urls: list):
    # divide urls
    valid_urls, invalid_urls = filter_valid_urls(urls)

    # if no any valid urls
    if len(valid_urls) == 0:
        tb_no_any_valid_urls_text = yaml_config().get_tb_no_any_valid_urls_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_no_any_valid_urls_text
        )
    elif len(invalid_urls) > 0:
        # show invalid urls text
        tb_invalid_urls_text = ""
        for invalid_url in invalid_urls:
            tb_invalid_urls_text += invalid_url + ": Invalid Url. \n"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_invalid_urls_text
        )
    else:
        accessible_urls, inaccessibale_urls = await filter_accessible_urls(valid_urls)

        # if no any accessable urls
        if len(accessible_urls) == 0:
            tb_no_any_accessible_urls_text = (
                yaml_config().get_tb_no_any_accessiable_urls_text()
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=tb_no_any_accessible_urls_text
            )
        elif len(inaccessibale_urls) > 0:
            tb_inaccessible_urls_text = ""
            for inaccessible_url in inaccessibale_urls:
                tb_inaccessible_urls_text += inaccessible_url + ": Cannot Access.\n"

            # TODO
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=tb_inaccessible_urls_text
            )

            await process_accessible_urls(update, context, urls=accessible_urls)
        else:
            await process_accessible_urls(update, context, urls=accessible_urls)


async def process_accessible_urls(
    update: Update, context: ContextTypes.DEFAULT_TYPE, urls: list
):
    logging.info("Processing accessible urls...")
    urls_ = reg_urls(urls=urls)

    # filter existing url
    db_path, table_name = setup_sqlite()
    ids_ = get_ids_by_urls_from_sqlite(
        db_path=db_path, table_name=table_name, urls=urls_
    )
    for url, id in zip(urls_, ids_):
        if id is not None:
            urls_.remove(url)

    for url in urls_:
        logging.info(f"***{url}")

    # no any existing urls
    if len(urls_) == 0:
        tb_no_new_urls_text = yaml_config().get_tb_no_any_new_urls_text()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=tb_no_new_urls_text,
        )
    else:
        # send "Processing urls..."
        tb_processing_urls_text = yaml_config().get_tb_processing_urls_text()
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tb_processing_urls_text
        )
        message_id = message.message_id

        titles, pcs = await get_titles_and_pcs_from_urls(urls=urls_)
        summaries = await get_summaries_by_urls_or_pcs(urls=urls_, pcs=pcs)
        current_time = get_current_time()
        times = [current_time] * len(urls_)
        tags = ["link"] * len(urls_)

        chroma_path = yaml_config().get_chroma_path()
        collection_name = yaml_config().get_chroma_collection_name()

        await insert_to_databases(
            update=update,
            context=context,
            message_id=message_id,
            db_path=db_path,
            table_name=table_name,
            chroma_path=chroma_path,
            collection_name=collection_name,
            urls=urls_,
            titles=titles,
            summaries=summaries,
            tags=tags,
            times=times,
        )


async def insert_to_databases(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_id,
    db_path,
    table_name,
    chroma_path,
    collection_name,
    urls,
    titles,
    summaries,
    tags,
    times,
    ctag="link",
):
    # insert to databases
    logging.info("Inserting to databases...")
    logging.info(
        f"{len(urls)}, {len(titles)}, {len(summaries)}, {len(tags)}, {len(times)}"
    )

    if len(urls) == len(titles) == len(summaries) == len(tags) == len(times):
        datas = merge_lists(urls, titles, summaries, tags, times)
        logging.info(f"{len(datas)}, {len(datas[0])}")
        tag_sqlite = insert_datas_to_sqlite(datas=datas)

        if tag_sqlite:
            ids = get_ids_by_urls_from_sqlite(
                db_path=db_path, table_name=table_name, urls=urls
            )
            if len(datas) == len(ids):
                tag_chroma = add_datas_to_chroma(
                    chroma_path=chroma_path,
                    collection_name=collection_name,
                    datas=datas,
                    ids=ids,
                    ctag=ctag,
                )
                if tag_chroma:
                    tb_urls_text = "Successfully added:\n"
                    tb_urls_text += res_2_markdown_text(
                        urls=urls, titles=titles, ids=ids, tag=ctag
                    )
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=message_id,
                        text=tb_urls_text,
                        parse_mode="MarkdownV2",
                    )
                else:
                    logging.error("Error occured in adding datas to chroma.")
            else:
                logging.error("Error occured in getting ids by urls from sqlite.")
        else:
            logging.error("Error occured in inserting datas to sqlite.")
    else:
        logging.error("Error occured in inserting to databases.")


def res_2_markdown_text(urls: list, titles: list, ids: list = None, tag: str = "link"):
    text = ""
    if tag == "link" or ids is None:
        for url, title in zip(urls, titles):
            url = add_preceding(url)
            title = add_preceding(title)
            text += f"\- [{title}]({url})\n"
        text += "Done\."
    else:
        db_path = yaml_config().get_sqlite_path()
        table_name = yaml_config().get_sqlite_table_name()

        for url, title, id in zip(urls, titles, ids):
            url = add_preceding(url)
            title = add_preceding(title)
            summary = add_preceding(
                get_row_by_id(db_path=db_path, table_name=table_name, id=id)[3]
            )
            text += f"\- [{title}]({url})\n{summary}\n\n"
        text += "Done\."
    return text


def add_preceding(text: str) -> str:
    to_preceding_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for char in to_preceding_chars:
        if char in text:
            text = text.replace(char, f"\\{char}")
    return text


async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chroma_path,
    collection_name,
    query_texts,
    message_id=None,
    n_results=3,
    tag="link",
):
    search_res = search_by_query_from_chroma(
        chroma_path=chroma_path,
        collection_name=collection_name,
        query_texts=query_texts,
        n_results=n_results,
        show_document=(tag != "link"),
    )
    await send_search_res(
        update=update,
        context=context,
        message_id=message_id,
        tag=tag,
        urls=search_res["urls"],
        titles=search_res["titles"],
        ids=(None if tag == "link" else search_res["ids"]),
    )


async def send_search_res(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_id=None,
    tag="link",
    urls=[],
    titles=[],
    ids=[],
):
    if len(urls) > 0 and len(titles) > 0:
        tb_urls_text = "Result:\n"
        tb_urls_text += res_2_markdown_text(urls=urls, titles=titles, ids=ids, tag=tag)
        if message_id is not None:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                text=tb_urls_text,
                message_id=message_id,
                parse_mode="MarkdownV2",
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=tb_urls_text,
                parse_mode="MarkdownV2",
            )
    else:
        tb_failed_to_search_text = yaml_config().get_tb_failed_to_search_text()
        if message_id is not None:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                text=tb_failed_to_search_text,
                message_id=message_id,
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=tb_failed_to_search_text
            )


def setup_telegram_bot_service():
    TELEGRAM_BOT_TOKEN = yaml_config().get_tb_token()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler("start", tb_start)
    help_handler = CommandHandler("help", tb_help)
    add_url_handler = CommandHandler("addurl", tb_add_url)
    add_note_handler = CommandHandler("addnote", tb_add_note)
    search_url_handler = CommandHandler("searchurl", tb_search_url)
    search_note_handler = CommandHandler("searchnote", tb_search_note)
    key_handler = CommandHandler("key", tb_key)
    more_handler = CommandHandler("more", tb_more)

    test_note_handler = CommandHandler("test", test_note)
    test_button_handler = CallbackQueryHandler(test_button)

    url_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), tb_urls)
    non_command_handler = MessageHandler(filters.COMMAND, tb_non_command)

    app.add_error_handler(tb_error)
    app.add_handler(start_handler)
    app.add_handler(help_handler)
    app.add_handler(add_url_handler)
    app.add_handler(add_note_handler)
    app.add_handler(search_url_handler)
    app.add_handler(search_note_handler)
    app.add_handler(key_handler)
    app.add_handler(more_handler)

    app.add_handler(test_note_handler)
    app.add_handler(test_button_handler)

    app.add_handler(url_handler)
    app.add_handler(non_command_handler)

    app.run_polling()
