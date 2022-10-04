import re
import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import dotenv_values

config = dotenv_values(".env")

API_TOKEN = config['BOT_API_KEY']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def get_data(url):
    res = {}
    res['state'] = False
    headers = {
        'User-Agent': 'My User Agent 1.0',
        'From': 'youremail@domain.com'  # This is another valid field
    }
    try:
        r = requests.get(url=url, headers=headers)
        res['state'] = True
        res['text'] = r.text
    except Exception as e:
        res['info'] = str(e)
        res['text'] = 'No info'
    return res


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer(
        "Привет {0}! Я помогу определить оператора и регион для номеров РФ. Пришли мне номер телефона в формате +79991234567".format(
            message.from_user.first_name))


@dp.message_handler()
async def other(message: types.Message):
    await bot.send_chat_action(message.from_user.id, 'typing')
    msg = re.sub('\s|[-]', '', message.text)
    check_num = bool(
        re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', msg)
    )
    if check_num:
        error_text = ''
        # phone_info = await check_phone_number(msg)
        msg = msg.replace('+7', '')
        phone_info = await get_data(f'https://zvonili.com/phone/+7{msg}')
        # answer_text = '<b>{2}</b>\n\n{0}\n{1}'.format(
        #     phone_info['operator'],
        #     phone_info['region'],
        #     phone_info['phone'],
        # )
        # print(phone_info['text'])
        if phone_info['state']:
            try:
                phone_check_info = re.sub(
                    '.?table.*[>]|[ <t].*[r]+[>]|[<td>]|[<span].*[\"]+[>]|[<span>]|[/][<span>]|[/][td>]|\s\s|^\s', '',
                    '<table class="mb-3">' + phone_info['text'].split('<table class="mb-3">')[1].split('</table>')[
                        0]).replace('  ', '\n')
                phone_operator_info = re.sub(
                    '.?table.*[>]|[ <t].*[r]+[>]|[<td>]|[<span].*[\"]+[>]|[<span>]|[/][<span>]|[/][td>]|\s\s|^\s', '',
                    phone_info['text'].split('Номер +')[1].split('</span>')[0]).replace('  ', '\n')
                answer_text = f'Номер +{phone_operator_info} \n<b>{phone_check_info}</b>'
            except Exception as e:
                answer_text = f'Номер +7{msg} \n<b>No info</b>'
                error_text = str(e)
        else:
            answer_text = phone_info['text']
            error_text = phone_info['error']
        await message.answer(answer_text, parse_mode=types.ParseMode.HTML)
        await bot.send_message(config['ADMIN_CHATID'], '@{0} ({1} {2} {3})\n{4}'.format(
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            message.from_user.id,
            f'{answer_text} {error_text}',
        ), parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('Похоже это не номер. \nПришли мне номер телефона в формате: \n\n<b>+79991234567</b>',
                             parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
