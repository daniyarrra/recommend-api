from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import urllib.request
import json
import random
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

# ── Translations for categories ──
CATEGORY_TRANSLATIONS = {
    "Фильмы":  {"ru": "Фильмы",  "en": "Movies",    "kz": "Фильмдер"},
    "Сериалы": {"ru": "Сериалы", "en": "TV Series",  "kz": "Сериалдар"},
    "Книги":   {"ru": "Книги",   "en": "Books",      "kz": "Кітаптар"},
    "Музыка":  {"ru": "Музыка",  "en": "Music",      "kz": "Музыка"},
}

# ── Hardcoded items with translations ──
hardcoded_items = [
    {
        "id": 1, 
        "title": "Interstellar", 
        "genre": "Sci-Fi", 
        "category": "Фильмы",
        "description": {
            "ru": "Когда засуха, пыльные бури и вымирание растений приводят человечество к кризису выживания, коллектив исследователей отправляется сквозь недавно обнаруженную червоточину.",
            "en": "When drought, dust storms and plant extinction push humanity to the brink, a team of explorers travels through a newly discovered wormhole in search of a new home.",
            "kz": "Құрғақшылық, шаң дауылдары және өсімдіктердің жойылуы адамзатты дағдарысқа алып келгенде, зерттеушілер тобы жаңадан табылған құрт тесігі арқылы жаңа мекен іздейді."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/c/c3/Interstellar_2014.jpg",
        "trailer_url": "https://www.youtube.com/embed/zSWdZVtXT7E",
        "cast": [{"name": "Мэттью Макконахи", "photo": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Matthew_McConaughey_-_Goldene_Kamera_2014_-_Berlin.jpg"}, {"name": "Энн Хэтэуэй", "photo": "https://upload.wikimedia.org/wikipedia/commons/e/e1/Anne_Hathaway_Face.jpg"}],
        "director": [{"name": "Кристофер Нолан", "photo": "https://upload.wikimedia.org/wikipedia/commons/9/95/Christopher_Nolan_Cannes_2018.jpg"}]
    },
    {
        "id": 4, 
        "title": "Dune: Part Two", 
        "genre": "Sci-Fi", 
        "category": "Фильмы",
        "description": {
            "ru": "Пол Атрейдес объединяется с Чани и фременами, отправляясь на тропу войны.",
            "en": "Paul Atreides unites with Chani and the Fremen as he sets out on a warpath.",
            "kz": "Пол Атрейдес Чани мен фременмен бірігіп, соғыс жолына шығады."
        },
        "image": "https://upload.wikimedia.org/wikipedia/en/8/8e/Dune_%282021_film%29.jpg",
        "trailer_url": "https://www.youtube.com/embed/Way9Dexny3w",
        "cast": [{"name": "Тимоти Шаламе", "photo": "https://upload.wikimedia.org/wikipedia/commons/4/43/Timoth%C3%A9e_Chalamet_2017_Berlin_Film_Festival.jpg"}, {"name": "Зендея", "photo": "https://upload.wikimedia.org/wikipedia/commons/2/28/Zendaya_-_2019_by_Glenn_Francis.jpg"}],
        "director": [{"name": "Дени Вильнёв", "photo": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Denis_Villeneuve_Cannes_2018.jpg"}]
    },
    {
        "id": 5, 
        "title": "The Dark Knight", 
        "genre": "Action", 
        "category": "Фильмы",
        "description": {
            "ru": "Бэтмен поднимает ставки в войне с криминалом с помощью лейтенанта Джима Гордона.",
            "en": "Batman raises the stakes in his war on crime with the help of Lieutenant Jim Gordon.",
            "kz": "Бэтмен лейтенант Джим Гордонның көмегімен қылмысқа қарсы соғыста ставкаларды көтереді."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/8/83/Dark_knight_rises_poster.jpg",
        "trailer_url": "https://www.youtube.com/embed/EXeTwQWrcwY"
    },
    {
        "id": 7, 
        "title": "Inception", 
        "genre": "Sci-Fi", 
        "category": "Фильмы",
        "description": {
            "ru": "Дом Кобб — талантливый вор в опасном искусстве извлечения: он крадет ценные секреты из подсознания.",
            "en": "Dom Cobb is a skilled thief in the dangerous art of extraction — stealing valuable secrets from deep within the subconscious.",
            "kz": "Дом Кобб — қауіпті өнер — экстракция саласындағы талантты ұры: ол ішкі санадан құнды құпияларды ұрлайды."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/b/bc/Poster_Inception_film_2010.jpg",
        "trailer_url": "https://www.youtube.com/embed/YoHD9XEInc0"
    },
    {
        "id": 9, 
        "title": "Spider-Man: Across the Spider-Verse", 
        "genre": "Animation", 
        "category": "Фильмы",
        "description": {
            "ru": "Майлз Моралес отправляется в приключение по мультивселенной.",
            "en": "Miles Morales embarks on an adventure across the Multiverse.",
            "kz": "Майлз Моралес мультиәлем бойынша шытырман оқиғаға аттанады."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/5/5b/Человек-паук_—_Паутина_вселенных.jpg",
        "trailer_url": "https://www.youtube.com/embed/cqGjhVJWtEg"
    },
    {
        "id": 20, 
        "title": "The Matrix", 
        "genre": "Sci-Fi", 
        "category": "Фильмы",
        "description": {
            "ru": "Хакер Нео узнает шокирующую правду о том, что весь мир — это компьютерная симуляция, и присоединяется к восстанию против машин.",
            "en": "Hacker Neo discovers the shocking truth that the entire world is a computer simulation and joins the rebellion against the machines.",
            "kz": "Хакер Нео бүкіл әлемнің компьютерлік симуляция екенін біліп, машиналарға қарсы көтерілісіне қосылады."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/b/ba/The_Matrix_Poster.jpg",
        "trailer_url": "https://www.youtube.com/embed/vKQi3bBA1y8"
    },
    {
        "id": 21, 
        "title": "Avengers: Endgame", 
        "genre": "Action", 
        "category": "Фильмы",
        "description": {
            "ru": "Оставшиеся в живых Мстители собираются вместе, чтобы отменить действия Таноса и восстановить баланс во Вселенной.",
            "en": "The surviving Avengers assemble once more to undo Thanos' actions and restore balance to the Universe.",
            "kz": "Аман қалған Кек алушылар Таностың іс-әрекетін жоюға және Ғаламдағы тепе-теңдікті қалпына келтіруге тырысады."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/4/4d/Avengers_Endgame_poster.jpg",
        "trailer_url": "https://www.youtube.com/embed/TcMBFSGVi1c"
    },
    {
        "id": 22, 
        "title": "Avatar", 
        "genre": "Sci-Fi", 
        "category": "Фильмы",
        "description": {
            "ru": "Парализованный морской пехотинец отправляется на луну Пандора для выполнения уникальной миссии.",
            "en": "A paraplegic Marine is dispatched to the moon Pandora on a unique mission.",
            "kz": "Мүгедек теңіз жаяу әскері Пандора айына ерекше миссияға жіберіледі."
        },
        "image": "https://m.media-amazon.com/images/M/MV5BNWI0Y2NkOWEtMmM2OC00MjQ3LWI1YzItZGQxYzQ3NzI4NWZmXkEyXkFqcGc@._V1_.jpg",
        "trailer_url": "https://www.youtube.com/embed/5PSNL1qE6VY"
    },
    {
        "id": 23, 
        "title": "Oppenheimer", 
        "genre": "Drama", 
        "category": "Фильмы",
        "description": {
            "ru": "История жизни американского физика Дж. Роберта Оппенгеймера, стоявшего во главе разработки атомной бомбы.",
            "en": "The life story of American physicist J. Robert Oppenheimer, who led the development of the atomic bomb.",
            "kz": "Атомдық бомбаны жасауды басқарған американдық физик Дж. Роберт Оппенгеймердің өмір тарихы."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/4/4a/Oppenheimer_%28film%29.jpg",
        "trailer_url": "https://www.youtube.com/embed/uYPbbksJxIg"
    },
    {
        "id": 24, 
        "title": "Gladiator", 
        "genre": "Action", 
        "category": "Фильмы",
        "description": {
            "ru": "Римский полководец Максимус, преданный своим императором, становится рабом и затем гладиатором.",
            "en": "Roman general Maximus, betrayed by his emperor, is reduced to slavery and becomes a gladiator.",
            "kz": "Рим қолбасшысы Максимус, императоры сатып кеткеннен кейін, құлға айналып, содан кейін гладиатор болады."
        },
        "image": "https://upload.wikimedia.org/wikipedia/ru/8/8d/Gladiator_vol1_1.jpg",
        "trailer_url": "https://www.youtube.com/embed/owK1qxDselE"
    },
]

# ── Harry Potter book translations ──
HP_TITLES = {
    0: {"ru": "Гарри Поттер и философский камень", "en": "Harry Potter and the Philosopher's Stone", "kz": "Гарри Поттер және пәлсапа тасы"},
    1: {"ru": "Гарри Поттер и Тайная комната", "en": "Harry Potter and the Chamber of Secrets", "kz": "Гарри Поттер және құпия бөлме"},
    2: {"ru": "Гарри Поттер и узник Азкабана", "en": "Harry Potter and the Prisoner of Azkaban", "kz": "Гарри Поттер және Азкабан тұтқыны"},
    3: {"ru": "Гарри Поттер и Кубок огня", "en": "Harry Potter and the Goblet of Fire", "kz": "Гарри Поттер және от тостағаны"},
    4: {"ru": "Гарри Поттер и Орден Феникса", "en": "Harry Potter and the Order of the Phoenix", "kz": "Гарри Поттер және Феникс ордені"},
    5: {"ru": "Гарри Поттер и Принц-полукровка", "en": "Harry Potter and the Half-Blood Prince", "kz": "Гарри Поттер және жартылай қанды ханзада"},
    6: {"ru": "Гарри Поттер и Дары Смерти", "en": "Harry Potter and the Deathly Hallows", "kz": "Гарри Поттер және өлім сыйлары"},
}

HP_DESCRIPTIONS = {
    0: {
        "ru": "Первая книга серии. Гарри Поттер узнаёт, что он волшебник, и отправляется в школу чародейства и волшебства Хогвартс. Автор: Дж. К. Роулинг.",
        "en": "The first book of the series. Harry Potter discovers he is a wizard and sets off for Hogwarts School of Witchcraft and Wizardry. Author: J.K. Rowling.",
        "kz": "Сериядағы бірінші кітап. Гарри Поттер өзінің сиқыршы екенін біліп, Хогвартс сиқыр мектебіне жол тартады. Автор: Дж. К. Роулинг."
    },
    1: {
        "ru": "Вторая книга серии. Гарри возвращается в Хогвартс, где таинственная сила нападает на учеников школы. Автор: Дж. К. Роулинг.",
        "en": "The second book. Harry returns to Hogwarts where a mysterious force is attacking students. Author: J.K. Rowling.",
        "kz": "Екінші кітап. Гарри Хогвартсқа оралады, мұнда жұмбақ күш оқушыларға шабуыл жасайды. Автор: Дж. К. Роулинг."
    },
    2: {
        "ru": "Третья книга серии. Из тюрьмы Азкабан сбегает опасный преступник Сириус Блэк, и Гарри оказывается в смертельной опасности. Автор: Дж. К. Роулинг.",
        "en": "The third book. Dangerous criminal Sirius Black escapes from Azkaban prison, putting Harry in mortal danger. Author: J.K. Rowling.",
        "kz": "Үшінші кітап. Қауіпті қылмыскер Сириус Блэк Азкабан түрмесінен қашады. Автор: Дж. К. Роулинг."
    },
    3: {
        "ru": "Четвёртая книга серии. Гарри неожиданно становится участником опасного Турнира Трёх Волшебников. Автор: Дж. К. Роулинг.",
        "en": "The fourth book. Harry unexpectedly becomes a participant in the dangerous Triwizard Tournament. Author: J.K. Rowling.",
        "kz": "Төртінші кітап. Гарри күтпеген жерден қауіпті Үш сиқыршы турнирінің қатысушысы болады. Автор: Дж. К. Роулинг."
    },
    4: {
        "ru": "Пятая книга серии. Гарри сталкивается с недоверием волшебного мира и создаёт тайную армию для борьбы с Волан-де-Мортом. Автор: Дж. К. Роулинг.",
        "en": "The fifth book. Harry faces disbelief from the wizarding world and creates a secret army to fight Voldemort. Author: J.K. Rowling.",
        "kz": "Бесінші кітап. Гарри сиқыр әлемінің сенімсіздігіне тап болады және Волан-де-Мортқа қарсы құпия армия құрады. Автор: Дж. К. Роулинг."
    },
    5: {
        "ru": "Шестая книга серии. Гарри узнаёт о прошлом Волан-де-Морта и находит загадочный учебник зельеварения. Автор: Дж. К. Роулинг.",
        "en": "The sixth book. Harry learns about Voldemort's past and finds a mysterious potions textbook. Author: J.K. Rowling.",
        "kz": "Алтыншы кітап. Гарри Волан-де-Морттың өткені туралы біліп, жұмбақ зелье оқулығын табады. Автор: Дж. К. Роулинг."
    },
    6: {
        "ru": "Седьмая и последняя книга серии. Гарри отправляется на поиски крестражей, чтобы уничтожить Волан-де-Морта раз и навсегда. Автор: Дж. К. Роулинг.",
        "en": "The seventh and final book. Harry sets out to find Horcruxes and destroy Voldemort once and for all. Author: J.K. Rowling.",
        "kz": "Жетінші және соңғы кітап. Гарри Волан-де-Мортты мәңгілікке жою үшін крестраждарды іздеуге шығады. Автор: Дж. К. Роулинг."
    },
}

HP_IMAGES = [
    "https://adebiportal.kz/storage/tmp/resize/books/1200_0_b90eafe8f449bea7bb5ac935fc076fe0.jpg",
    "https://cdn.azbooka.ru/cv/w1100/webp/127e66a9-a929-4330-87fd-c718a21d4238.webp",
    "https://cdn.azbooka.ru/cv/w1100/cfbde54d-3725-4dce-ac99-57692ac4dabb.jpg",
    "https://cdn.azbooka.ru/cv/w1100/4a78131f-c93d-4a49-a0b2-e52581308918.jpg",
    "https://adebiportal.kz/storage/tmp/resize/books/1200_0_9a4ac61ef4ce608e7918c68c2a915973.jpg",
    "https://loveread.ec/img/book_covers/002/2322.jpg",
    "https://cdn.azbooka.ru/cv/w1100/54acc1e5-bff7-448c-a10b-a4ee7aa74292.jpg",
]

# ── Music description templates ──
MUSIC_DESC = {
    "ru": "Популярный трек в жанре {genre}. Исполнитель: {artist}.",
    "en": "Popular track in the {genre} genre. Artist: {artist}.",
    "kz": "{genre} жанрындағы танымал трек. Орындаушы: {artist}.",
}

MUSIC_DESC_ALT = {
    "ru": "Потрясающий трек в жанре {genre}. Исполнитель: {artist}.",
    "en": "Amazing track in the {genre} genre. Artist: {artist}.",
    "kz": "{genre} жанрындағы тамаша трек. Орындаушы: {artist}.",
}

ITEMS_FILE = os.path.join(os.path.dirname(__file__), 'items.json')

def load_custom_items():
    """Load admin-added items from JSON file."""
    try:
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_custom_items(items):
    """Save admin-added items to JSON file."""
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def get_next_custom_id():
    """Get the next available ID for custom items (starting from 1000)."""
    items = load_custom_items()
    if not items:
        return 1000
    return max(i['id'] for i in items) + 1

cached_items = []

def fetch_external_data():
    global cached_items
    if cached_items:
        custom = load_custom_items()
        custom_dict = {ci['id']: ci for ci in custom}
        base = [i for i in cached_items if i.get('_source') != 'custom' and i['id'] not in custom_dict]
        for ci in custom:
            ci['_source'] = 'custom'
        return base + custom
        
    items = []
    items.extend(hardcoded_items)
    
    current_id = 100

    # 1. Сериалы (Hardcoded with Translations and Trailers)
    hardcoded_shows = [
        {
            "id": current_id,
            "title": "Breaking Bad",
            "genre": "Drama",
            "category": "Сериалы",
            "description": {
                "ru": "У школьного учителя химии Уолтера Уайта диагностируют неоперабельный рак легких. Чтобы обеспечить финансовое будущее своей семьи, он решает производить и продавать метамфетамин.",
                "en": "A high school chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine in order to secure his family's future.",
                "kz": "Мектептегі химия пәнінің мұғалімі Уолтер Уайт өкпе қатерлі ісігіне шалдыққанын біледі. Отбасының қаржылық болашағын қамтамасыз ету үшін ол метамфетамин өндіріп, сатуды ұйғарады."
            },
            "image": "https://m.media-amazon.com/images/M/MV5BMzU5ZGYzNmQtMTdhYy00OGRiLTg0NmQtYjVjNzliZTg1ZGE4XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
            "trailer_url": "https://www.youtube.com/embed/HhesaQXLuRY"
        },
        {
            "id": current_id + 1,
            "title": "Game of Thrones",
            "genre": "Fantasy",
            "category": "Сериалы",
            "description": {
                "ru": "Девять благородных семей сражаются за контроль над мифическими землями Вестероса, в то время как древний враг возвращается после тысячелетий спячки.",
                "en": "Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for millennia.",
                "kz": "Тоғыз ақсүйек отбасы Вестерос жерлерін бақылау үшін күреседі, ал мыңдаған жылдар бойы ұйықтап жатқан көне жау қайта оралады."
            },
            "image": "https://kinocensor.ru/cache/videos/78/fcb0e920ed44b9d3ae610ea8e6a568b4-1200x1800.jpg",
            "trailer_url": "https://www.youtube.com/embed/KPLWWIOCOOQ"
        },
        {
            "id": current_id + 2,
            "title": "Stranger Things",
            "genre": "Sci-Fi",
            "category": "Сериалы",
            "description": {
                "ru": "Когда исчезает маленький мальчик, его мать, начальник полиции и его друзья должны столкнуться с ужасающими сверхъестественными силами, чтобы вернуть его.",
                "en": "When a young boy disappears, his mother, a police chief and his friends must confront terrifying supernatural forces in order to get him back.",
                "kz": "Кішкентай бала жоғалып кеткенде, оның анасы, полиция бастығы және достары оны қайтару үшін қорқынышты табиғаттан тыс күштермен бетпе-бет келуі керек."
            },
            "image": "https://upload.wikimedia.org/wikipedia/en/b/b1/Stranger_Things_season_1.jpg",
            "trailer_url": "https://www.youtube.com/embed/b9EkMc79ZSU"
        },
        {
            "id": current_id + 3,
            "title": "The Office",
            "genre": "Comedy",
            "category": "Сериалы",
            "description": {
                "ru": "Псевдодокументальный сериал о повседневной жизни офисных сотрудников филиала бумажной компании Dunder Mifflin в Скрантоне.",
                "en": "A mockumentary on a group of typical office workers, where the workday consists of ego clashes, inappropriate behavior, and tedium.",
                "kz": "Скрантондағы Dunder Mifflin қағаз компаниясы филиалының кеңсе қызметкерлерінің күнделікті өмірі туралы псевдодеректі сериал."
            },
            "image": "https://m.media-amazon.com/images/I/81dlW8jFJYL._AC_UF894,1000_QL80_.jpg",
            "trailer_url": "https://www.youtube.com/embed/c0q1A3h7_Fw"
        },
        {
            "id": current_id + 4,
            "title": "Chernobyl",
            "genre": "Drama",
            "category": "Сериалы",
            "description": {
                "ru": "В апреле 1986 года произошел взрыв на Чернобыльской атомной электростанции, став одной из самых страшных техногенных катастроф в истории.",
                "en": "In April 1986, an explosion at the Chernobyl nuclear power plant in the Union of Soviet Socialist Republics becomes one of the world's worst man-made catastrophes.",
                "kz": "1986 жылдың сәуір айында Чернобыль атом электр станциясында жарылыс болып, тарихтағы ең жаман техногендік апаттардың біріне айналды."
            },
            "image": "https://upload.wikimedia.org/wikipedia/en/a/a7/Chernobyl_2019_Miniseries.jpg",
            "trailer_url": "https://www.youtube.com/embed/s9APLXM9Ei8"
        }
    ]
    
    items.extend(hardcoded_shows)
    current_id += 5

    # 2. Книги — Гарри Поттер (все части)
    for i in range(7):
        items.append({
            "id": current_id + i,
            "title": HP_TITLES[i],
            "genre": "Fantasy",
            "category": "Книги",
            "description": HP_DESCRIPTIONS[i],
            "image": HP_IMAGES[i]
        })
    current_id += 7

    # Build seen_titles to avoid duplicates
    seen_titles = set()
    for item in items:
        t = item.get('title', '')
        if isinstance(t, dict):
            t = t.get('en', t.get('ru', ''))
        seen_titles.add(t.lower().strip())

    # 2.5 Загрузка Фильмов (iTunes Top Movies)
    try:
        req = urllib.request.Request("https://itunes.apple.com/us/rss/topmovies/limit=100/json", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for movie in data.get('feed', {}).get('entry', []):
                title = movie.get('im:name', {}).get('label', 'Unknown')
                if title.lower().strip() in seen_titles:
                    continue
                seen_titles.add(title.lower().strip())
                genre = movie.get('category', {}).get('attributes', {}).get('label', 'Movie')
                summary = movie.get('summary', {}).get('label', '')
                
                images = movie.get('im:image', [])
                img_url = images[-1].get('label') if images else ""
                if img_url:
                    img_url = img_url.replace("170x170bb", "600x600bb").replace("113x170bb", "400x600bb")
                else:
                    img_url = "https://via.placeholder.com/500x750?text=Movie"

                trailer_url = ""
                links = movie.get('link', [])
                if isinstance(links, list):
                    for link in links:
                        if link.get('attributes', {}).get('type', '').startswith('video'):
                            trailer_url = link['attributes']['href']
                            break
                elif isinstance(links, dict):
                    if links.get('attributes', {}).get('type', '').startswith('video'):
                        trailer_url = links['attributes']['href']

                items.append({
                    "id": current_id,
                    "title": title,
                    "genre": genre,
                    "category": "Фильмы",
                    "description": {
                        "ru": summary,
                        "en": summary,
                        "kz": summary
                    },
                    "image": img_url,
                    "trailer_url": trailer_url
                })
                current_id += 1
    except Exception as e:
        print("Ошибка загрузки фильмов:", e)

    # 2.6 Загрузка Сериалов (iTunes Top TV Seasons)
    try:
        req = urllib.request.Request("https://itunes.apple.com/us/rss/toptvseasons/limit=100/json", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for show in data.get('feed', {}).get('entry', []):
                title = show.get('im:name', {}).get('label', 'Unknown')
                if title.lower().strip() in seen_titles:
                    continue
                seen_titles.add(title.lower().strip())

                genre = show.get('category', {}).get('attributes', {}).get('label', 'TV')
                summary = show.get('summary', {}).get('label', '')
                
                images = show.get('im:image', [])
                img_url = images[-1].get('label') if images else ""
                if img_url:
                    img_url = img_url.replace("170x170bb", "600x600bb").replace("113x170bb", "400x600bb")
                else:
                    img_url = "https://via.placeholder.com/500x750?text=TV+Show"

                items.append({
                    "id": current_id,
                    "title": title,
                    "genre": genre,
                    "category": "Сериалы",
                    "description": {
                        "ru": summary,
                        "en": summary,
                        "kz": summary
                    },
                    "image": img_url,
                    "trailer_url": ""
                })
                current_id += 1
    except Exception as e:
        print("Ошибка загрузки сериалов:", e)

    # 3. Загрузка Музыки (iTunes Top Songs)
    try:
        req = urllib.request.Request("https://itunes.apple.com/us/rss/topsongs/limit=100/json", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for song in data.get('feed', {}).get('entry', []):
                title = song.get('title', {}).get('label', 'Unknown').split(' - ')[0]
                if title.lower().strip() in seen_titles:
                    continue
                seen_titles.add(title.lower().strip())
                genre = song.get('category', {}).get('attributes', {}).get('label', 'Music')
                artist = song.get('im:artist', {}).get('label', 'Unknown Artist')
                
                # Достаем самую качественную картинку
                images = song.get('im:image', [])
                img_url = images[-1].get('label') if images else ""
                if img_url:
                    img_url = img_url.replace("170x170bb.png", "600x600bb.jpg")
                    img_url = img_url.replace("170x170bb.webp", "600x600bb.jpg")
                else:
                    img_url = "https://via.placeholder.com/500x750?text=Music"

                # Извлекаем превью (30 секунд аудио)
                preview_url = ""
                links = song.get('link', [])
                for link in links:
                    if link.get('attributes', {}).get('type', '').startswith('audio'):
                        preview_url = link['attributes']['href']
                        break

                items.append({
                    "id": current_id,
                    "title": title,
                    "genre": genre,
                    "category": "Музыка",
                    "description": {
                        lang: MUSIC_DESC[lang].format(genre=genre, artist=artist)
                        for lang in ("ru", "en", "kz")
                    },
                    "image": img_url,
                    "preview_url": preview_url
                })
                current_id += 1
    except Exception as e:
        print("Ошибка загрузки музыки:", e)

    # 4. Загрузка Tame Impala
    try:
        req = urllib.request.Request("https://itunes.apple.com/search?term=tame+impala&entity=song&limit=12", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for track in data.get('results', []):
                title = track.get('trackName', 'Unknown')
                genre = track.get('primaryGenreName', 'Alternative')
                artist = track.get('artistName', 'Tame Impala')
                img_url = track.get('artworkUrl100', '').replace('100x100bb', '600x600bb') if track.get('artworkUrl100') else "https://placehold.co/500x750/0f172a/fff?text=No+Cover"
                preview_url = track.get('previewUrl', '')

                items.append({
                    "id": current_id,
                    "title": title,
                    "genre": genre,
                    "category": "Музыка",
                    "description": {
                        lang: MUSIC_DESC_ALT[lang].format(genre=genre, artist=artist)
                        for lang in ("ru", "en", "kz")
                    },
                    "image": img_url,
                    "preview_url": preview_url
                })
                current_id += 1
    except Exception as e:
        print("Ошибка загрузки Tame Impala:", e)

    # Mark all non-custom items
    for item in items:
        item['_source'] = 'builtin'

    # Add custom (admin-added/edited) items
    custom = load_custom_items()
    custom_dict = {}
    for ci in custom:
        ci['_source'] = 'custom'
        custom_dict[ci['id']] = ci
        
    final_items = []
    for item in items:
        if item['id'] in custom_dict:
            continue
        final_items.append(item)
        
    final_items.extend(custom)

    cached_items = final_items
    return final_items


def localize_item(item, lang):
    """Resolve multilingual fields to a single language."""
    result = dict(item)
    
    # Remove internal fields
    result.pop('_source', None)
    
    # Resolve description
    desc = result.get("description", "")
    if isinstance(desc, dict):
        result["description"] = desc.get(lang, desc.get("ru", ""))
    
    # Resolve title (for HP books)
    title = result.get("title", "")
    if isinstance(title, dict):
        result["title"] = title.get(lang, title.get("ru", ""))
    
    # Resolve category
    cat = result.get("category", "")
    if cat in CATEGORY_TRANSLATIONS:
        result["category"] = CATEGORY_TRANSLATIONS[cat].get(lang, cat)
    
    return result


@app.route("/items")
def get_items():
    lang = request.args.get("lang", "ru")
    ids = request.args.get("ids")
    items = fetch_external_data()
    
    if ids:
        try:
            id_list = [int(i) for i in ids.split(",") if i.strip()]
            items = [item for item in items if item["id"] in id_list]
        except ValueError:
            pass # Ignore invalid id format
            
    return jsonify([localize_item(item, lang) for item in items])

@app.route("/items/<int:item_id>")
def get_item_by_id(item_id):
    lang = request.args.get("lang", "ru")
    items = fetch_external_data()
    item = next((i for i in items if i["id"] == item_id), None)
    if item:
        return jsonify(localize_item(item, lang))
    return jsonify({"error": "Item not found"}), 404

@app.route("/rate", methods=["POST"])
def rate():
    data = request.json
    print(data)
    return jsonify({"message": "ok"})

@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    lang = request.args.get("lang", "ru")
    items = fetch_external_data()
    
    if request.method == "POST" and request.is_json and os.getenv("GEMINI_API_KEY"):
        data = request.json
        liked_titles = data.get("liked_titles", [])
        watchlist_titles = data.get("watchlist_titles", [])
        
        if liked_titles or watchlist_titles:
            catalog_summary = []
            for i in items:
                title = i.get('title')
                if isinstance(title, dict):
                    title = title.get("en", title.get("ru", ""))
                catalog_summary.append(f"{i['id']}: {title} ({i['genre']})")
                
            prompt = f"""
You are a media recommendation engine.
User likes these items: {', '.join(liked_titles) if liked_titles else 'None specified'}
User wants to watch/read/listen to: {', '.join(watchlist_titles) if watchlist_titles else 'None specified'}

Here is our catalog (ID: Title):
{chr(10).join(catalog_summary)}

Select 6 DIFFERENT items from the catalog that the user would enjoy the most. 
For each selected item, provide its exact integer ID from the catalog, and a short, 1-2 sentence personalized explanation of why they will like it.
The explanation MUST be written in {lang} language.

Respond ONLY with a valid JSON array of objects, with no markdown formatting or backticks.
Format:
[
  {{"id": 123, "ai_reason": "Explanation in requested language..."}}
]
"""
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3].strip()
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3].strip()
                    
                ai_recs = json.loads(response_text)
                
                final_recs = []
                for rec in ai_recs:
                    item_id = rec.get("id")
                    matched_item = next((i for i in items if i["id"] == item_id), None)
                    if matched_item:
                        loc_item = localize_item(matched_item, lang)
                        loc_item["ai_reason"] = rec.get("ai_reason")
                        final_recs.append(loc_item)
                        
                if final_recs:
                    return jsonify(final_recs)
                    
            except Exception as e:
                print("Gemini API Error:", e)
                # Fallback to random if AI fails
                pass

    # Fallback to random
    recommendations = random.sample(items, min(6, len(items)))
    return jsonify([localize_item(item, lang) for item in recommendations])

@app.route("/login", methods=["POST"])
def login():
    return jsonify({"token": "123"})

@app.route("/register", methods=["POST"])
def register():
    return jsonify({"message": "registered"})

# ══════════════════════════════════════════
# Admin API — Content Management (CRUD)
# ══════════════════════════════════════════

@app.route("/admin/items", methods=["POST"])
def admin_create_item():
    """Create a new content item."""
    data = request.json
    if not data or not data.get('title') or not data.get('genre') or not data.get('category'):
        return jsonify({"error": "Missing required fields"}), 400

    new_item = {
        "id": get_next_custom_id(),
        "title": data['title'],
        "genre": data['genre'],
        "category": data['category'],
        "description": {
            "ru": data.get('description_ru', ''),
            "en": data.get('description_en', ''),
            "kz": data.get('description_kz', '')
        },
        "image": data.get('image', ''),
        "trailer_url": data.get('trailer_url', ''),
        "preview_url": data.get('preview_url', ''),
        "artist": data.get('artist', ''),
        "cast": data.get('cast', ''),
        "director": data.get('director', ''),
        "is_featured": data.get('is_featured', False)
    }

    items = load_custom_items()
    items.append(new_item)
    save_custom_items(items)

    # Clear cache so new items are picked up
    global cached_items
    cached_items = []

    return jsonify(new_item), 201


@app.route("/admin/items/<int:item_id>", methods=["PUT"])
def admin_update_item(item_id):
    """Update an existing content item."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    items = load_custom_items()
    item = next((i for i in items if i['id'] == item_id), None)

    if item:
        # Update custom item
        item['title'] = data.get('title', item['title'])
        item['genre'] = data.get('genre', item['genre'])
        item['category'] = data.get('category', item['category'])
        item['description'] = {
            "ru": data.get('description_ru', item.get('description', {}).get('ru', '')),
            "en": data.get('description_en', item.get('description', {}).get('en', '')),
            "kz": data.get('description_kz', item.get('description', {}).get('kz', ''))
        }
        item['image'] = data.get('image', item.get('image', ''))
        item['trailer_url'] = data.get('trailer_url', item.get('trailer_url', ''))
        item['preview_url'] = data.get('preview_url', item.get('preview_url', ''))
        item['artist'] = data.get('artist', item.get('artist', ''))
        item['cast'] = data.get('cast', item.get('cast', ''))
        item['director'] = data.get('director', item.get('director', ''))
        if 'is_featured' in data:
            item['is_featured'] = data['is_featured']
        save_custom_items(items)
    else:
        # Item is hardcoded — create a custom override
        new_item = {
            "id": item_id,
            "title": data.get('title', ''),
            "genre": data.get('genre', ''),
            "category": data.get('category', ''),
            "description": {
                "ru": data.get('description_ru', ''),
                "en": data.get('description_en', ''),
                "kz": data.get('description_kz', '')
            },
            "image": data.get('image', ''),
            "trailer_url": data.get('trailer_url', ''),
            "preview_url": data.get('preview_url', ''),
            "artist": data.get('artist', ''),
            "cast": data.get('cast', ''),
            "director": data.get('director', ''),
            "is_featured": data.get('is_featured', False)
        }
        items.append(new_item)
        save_custom_items(items)

    global cached_items
    cached_items = []

    return jsonify({"message": "updated"})


@app.route("/admin/items/<int:item_id>", methods=["DELETE"])
def admin_delete_item(item_id):
    """Delete a content item."""
    items = load_custom_items()
    new_items = [i for i in items if i['id'] != item_id]

    if len(new_items) == len(items):
        return jsonify({"error": "Item not found or is a built-in item"}), 404

    save_custom_items(new_items)

    global cached_items
    cached_items = []

    return jsonify({"message": "deleted"})


@app.route("/admin/upload", methods=["POST"])
def admin_upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Handle duplicate filenames
        base, extension = os.path.splitext(filename)
        counter = 1
        final_filename = filename
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], final_filename)):
            final_filename = f"{base}_{counter}{extension}"
            counter += 1
            
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], final_filename))
        # Build URL dynamically based on request host
        file_url = f"{request.scheme}://{request.host}/uploads/{final_filename}"
        return jsonify({"url": file_url}), 200
    return jsonify({"error": "File type not allowed"}), 400

@app.route("/admin/ai-fill", methods=["POST"])
def admin_ai_fill():
    """Generate content descriptions using Gemini AI."""
    data = request.json
    title = data.get('title')
    category = data.get('category')
    
    if not title or not category:
        return jsonify({"error": "Title and category are required"}), 400
        
    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"error": "Gemini API key is not configured"}), 500
        
    prompt = f"""
    You are an expert content editor for an entertainment catalog.
    Please write engaging descriptions for the following item:
    Title: "{title}"
    Category: "{category}"
    
    Provide the response ONLY in the following JSON format, without any markdown formatting or backticks:
    {{
        "genre": "Comma separated genres (e.g., Sci-Fi, Drama)",
        "description_ru": "A catchy description in Russian (about 2-3 sentences).",
        "description_en": "A catchy description in English (about 2-3 sentences).",
        "description_kz": "A catchy description in Kazakh (about 2-3 sentences)."
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up possible markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        return jsonify(result), 200
    except Exception as e:
        print("AI Gen Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    lang = request.args.get("lang", "ru")
    data = request.json
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
        
    items = fetch_external_data()
    catalog_summary = []
    for i in items:
        title = i.get('title')
        if isinstance(title, dict):
            title = title.get("en", title.get("ru", ""))
        catalog_summary.append(f"{i['id']}: {title} ({i['genre']}, {i['category']})")
        
    prompt = f"""
You are a helpful and enthusiastic media recommendation AI assistant.
The user sent the following message: "{message}"

Here is our catalog (ID: Title (Genre, Category)):
{chr(10).join(catalog_summary)}

Respond ONLY with a valid JSON object, with no markdown formatting or backticks.
The JSON must have two fields:
1. "reply": A natural, conversational response to the user's message in the {lang} language. Acknowledge what they asked for and introduce the recommendations if you found any. Be friendly and concise.
2. "item_ids": An array of integer IDs of up to 4 items from the catalog that best match their request. If nothing matches perfectly, provide the closest matches. If it's a general question without needing items, leave the array empty.

Format:
{{
  "reply": "Отличный выбор! Вот несколько бодрящих треков для вашей тренировки:",
  "item_ids": [100, 101, 102]
}}
"""
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return jsonify({
                "reply": "К сожалению, AI отключен (нет API ключа). Но я все равно рад вас видеть!", 
                "items": []
            })
            
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        ai_response = json.loads(response_text)
        
        # Populate items
        recommended_items = []
        for item_id in ai_response.get("item_ids", []):
            matched_item = next((i for i in items if i["id"] == item_id), None)
            if matched_item:
                recommended_items.append(localize_item(matched_item, lang))
                
        return jsonify({
            "reply": ai_response.get("reply", ""),
            "items": recommended_items
        })
    except Exception as e:
        print("Chat API Error:", e)
        return jsonify({"error": "Failed to process chat message"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)