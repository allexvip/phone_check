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

async def check_zvonili(phone):
    result_str = ''
    phone = re.sub('^(\+7|7|8)', '', phone)
    headers = {
        'User-Agent': 'My User Agent 1.0',
        'From': 'youremail@domain.com'  # This is another valid field
    }
    try:
        if len(phone) == 10:
            r = requests.get('https://zvonili.com/phone/+7{0}'.format(
                phone
            ), headers=headers)
            html = r.text
            result_str = re.sub('.?table.*[>]|[ <t].*[r]+[>]|[<td>]|[<span].*[\"]+[>]|[<span>]|[/][<span>]|[/][td>]|\s\s|^\s','','<table class="mb-3">'+html.split('<table class="mb-3">')[1].split('</table>')[0]).replace('  ','\n')
        else:
            result_str = 'No info'
    except:
        result_str = 'No info'
    return result_str

async def check_phone_number(phone):
    result = {}
    phone = re.sub('^(\+7|7|8)', '', phone)
    if len(phone) == 10:
        r = requests.get('{1}{0}'.format(
            phone,
            config['PHONE_CHECK_URL'],
        ))
        html = r.text
        result['phone'] = '+7{0} {1}'.format(phone,await check_zvonili(phone))
        result['operator'] = html.split('Оператор: ')[1].split('<br>')[0]
        result['region'] = html.split('Регион: ')[1].split('"')[0].split('<br>')[0]
    else:
        result['phone'] = '+7{0}'.format(phone)
        result['operator'] = 'Неправильный формат номера.'
        result['region'] = 'Пришли мне номер телефона в формате +79991234567.'
    return result


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
    check_num = bool(
        re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', message.text)
    )
    if check_num:
        phone_info = await check_phone_number(message.text)
        answer_text = '<b>{2}</b>\n\n{0}\n{1}'.format(
            phone_info['operator'],
            phone_info['region'],
            phone_info['phone'],
        )
        await message.answer(answer_text, parse_mode=types.ParseMode.HTML)
        await bot.send_message(config['ADMIN_CHATID'],'@{0} ({1} {2} {3})\n{4}'.format(
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            message.from_user.id,
            answer_text,
        ),parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('Похоже это не номер. \nПришли мне номер телефона в формате: \n\n<b>+79991234567</b>',
                             parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
