import os
import requests
import re
from chuo_line_specialist import check_chuo_line_train
from co_line_specialist import check_co_line_train
from tokaido_line_specialist import check_tokaido_line_train
from boso_specialist import check_boso_train
from tohoku_specialist import check_tohoku_train
from suka_specialist import check_suka_line_train

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train"

STATION_DICT = {
    # --- JR山手線 ---
    'Osaki': '大崎', 'Gotanda': '五反田', 'Meguro': '目黒', 'Ebisu': '恵比寿',
    'Shibuya': '渋谷', 'Harajuku': '原宿', 'Yoyogi': '代々木', 'Shinjuku': '新宿',
    'ShinOkubo': '新大久保', 'Takadanobaba': '高田馬場', 'Mejiro': '目白',
    'Ikebukuro': '池袋', 'Otsuka': '大塚', 'Sugamo': '巣鴨', 'Komagome': '駒込',
    'Tabata': '田端', 'NishiNippori': '西日暮里', 'Nippori': '日暮里',
    'Uguisudani': '鶯谷', 'Ueno': '上野', 'Okachimachi': '御徒町',
    'Akihabara': '秋葉原', 'Kanda': '神田', 'Tokyo': '東京', 'Yurakucho': '有楽町',
    'Shimbashi': '新橋', 'Hamamatsucho': '浜松町', 'Tamachi': '田町',
    'TakanawaGateway': '高輪ｹﾞｰﾄｳｪｲ', 'Shinagawa': '品川',

    #中央快速線(大月以東)
    'Tokyo': '東京', 'Kanda': '神田', 'Ochanomizu': '御茶ノ水', 'Yotsuya': '四ツ谷', 
    'Shinjuku': '新宿', 'Nakano': '中野', 'Koenji': '高円寺', 'Asagaya': '阿佐ヶ谷', 
    'Ogikubo': '荻窪', 'NishiOgikubo': '西荻窪', 'Kichijoji': '吉祥寺', 'Mitaka': '三鷹', 
    'MusashiSakai': '武蔵境', 'HigashiKoganei': '東小金井', 'MusashiKoganei': '武蔵小金井', 
    'Kokubunji': '国分寺', 'NishiKokubunji': '西国分寺', 'Kunitachi': '国立', 
    'Tachikawa': '立川', 'Hino': '日野', 'Toyoda': '豊田', 'Hachioji': '八王子', 
    'NishiHachioji': '西八王子', 'Takao': '高尾', 'Sagamiko': '相模湖', 'Fujino': '藤野', 
    'Uenohara': '上野原', 'Shiotsu': '四方津', 'Yanagawa': '梁川', 'Torisawa': '鳥沢', 
    'Saruhashi': '猿橋', 'Otsuki': '大月',

    #青梅五日市線
    'NishiTachikawa': '西立川', 'HigashiNakagami': '東中神', 'Nakagami': '中神', 
    'Akishima': '昭島', 'Haijima': '拝島', 'Ushihama': '牛浜', 'Fussa': '福生', 
    'Hamura': '羽村', 'Ozaku': '小作', 'Kabe': '河辺', 'HigashiOme': '東青梅', 
    'Ome': '青梅', 'Miyanohira': '宮ノ平', 'Hinatawada': '日向和田', 'Ishigamimae': '石神前', 
    'Futamatao': '二俣尾', 'Ikusabata': '軍畑', 'Sawai': '沢井', 'Mitake': '御嶽', 
    'Kawai': '川井', 'Kori': '古里', 'Hatonosu': '鳩ノ巣', 'Shiromaru': '白丸', 
    'OkuTama': '奥多摩', 'Kumagawa': '熊川', 'HigashiAkiru': '東秋留', 
    'Akigawa': '秋川', 'MusashiHikida': '武蔵引田', 'MusashiMasuko': '武蔵増戸', 
    'MusashiItsukaichi': '武蔵五日市',

    #富士急行線(主要駅)
    'Tsurushi': '都留市', 'Tsurubunkadaigakumae': '都留文科大学前', 'Gekkouji': '月江寺', 
    'Shimoyoshida': '下吉田', 'Fujisan': '富士山', 'FujikyuHighland': '富士急ハイランド', 
    'Kawaguchiko': '河口湖',

    #中央本線
    'Hatsukari' : '初狩', 'Sasago': '笹子', 'KaiYamato': '甲斐大和', 'KatsunumaBudokyo': '勝沼ぶどう郷',
    'Enzan': '塩山', 'HigashiYamanashi': '東山梨', 'Yamanashishi': '山梨市', 'Kasugaicho': '春日居町',
    'IsaawaOnsen': '石和温泉', 'Sakaori': '酒折', 'Kofu': '甲府', 'Ryuo': '竜王', 'Nirasaki': '韮崎',  
    'Shinpu': '新府', 'Anayama': '穴山', 'Hinoharu': '日野春', 'Nagasaka': '長坂', 'Kobuchizawa': '小淵沢',
    'Shinanosakai': '信濃境', 'Fujimi': '富士見', 'Suzurannosato': 'すずらんの里', 'Aoyagi': '青柳', 
    'Chino': '茅野', 'KamiSuwa': '上諏訪', 'ShimoSuwa': '下諏訪', 'Okaya': '岡谷', 'Kawagishi': '川岸',
    'Tatsuno': '辰野', 'ShinanoKawashima': '信濃川島', 'Ono': '小野', 'Midoriko': 'みどり湖', 
    'Shiojiri': '塩尻', 'Hirooka': '広丘', 'Murai': '村井', 'Hirata': '平田', 
    'MinamiMatsumoto': '南松本', 'Matsumoto': '松本',

    #大糸線(主要駅)
    'ShinanoOmachi': '信濃大町', 'Hakuba': '白馬', 'MinamiOtari': '南小谷',

    #篠ノ井線
    'Tazawa': '田沢', 'Akashina': '明科', 'Saijo': '西条', 'Sakakita': '坂北', 'Hijirikogen': '聖高原',
    'Kamuriki': '冠着', 'Obasute': '姨捨', 'Inariyama': '稲荷山', 'Shinonoi': '篠ノ井',
    'Imai': '今井', 'Kawanakajima': '川中島', 'Amori': '安茂里', 'Nagano': '長野',
    

    #鹿島線
    'KashimaSoccerStudium': '鹿島サッカースタジアム', 'KashimaJingu': '鹿島神宮', 'Nobukata': '延方', 
    'Itako': '潮来', 'Junikyo': '十二橋', 'Katori': '香取',

    #外房線
    'HonChiba': '本千葉', 'Kamatori': '鎌取', 'Honda': '誉田', 'Toke': '土気', 'Oami':'大網', 
    'Nagata': '永田', 'Honnou': '本納', 'ShinMobara': '新茂原', 'Mobara': '茂原', 'Yatsumi': '八積',
    'KazusaIchinoiya': '上総一ノ宮', 'Torami': '東浪見', 'Taito': '太東', 'Chojamachi': '長者町',
    'Mikado': '三門', 'Nanihana': '浪花', 'Onjuku': '御宿', 'Ubara': '鵜原',
    'KazusaOkitsu': '上総興津', 'YukawaIsland': '行川アイランド', 'AwaKominato': '安房小湊',
    'AwaAmatsu': '安房天津', 'AwaKamogawa': '安房鴨川',

    #内房線
    'Hamano': '浜野', 'Yawatajuku': '八幡宿', 'Goi': '五井', 'Anegasaki': '姉ヶ崎', 'Nagaura': '長浦',
    'Sodegaura': '袖ケ浦', 'Iwane': '巌根', 'Kisarazu': '木更津', 'Kimitsu': '君津', 'Aohori': '青堀',
    'Onuki': '大貫', 'Sanukimachi': '佐貫町', 'KazusaMinato': '上総湊', 'Takeoka': '竹岡',
    'HamaKanaya': '浜金谷', 'Hota': '保田', 'AwaKatsuyama': '安房勝山', 'Iwai': '岩井',
    'Tomiura': '富浦', 'Nakofunagata': '那古船形', 'Tateyama': '館山', 'Kokonoe': '九重',
    'Chikura': '千倉', 'Chitose': '千歳', 'Minamihara': '南三原', 'Wadaura': '和田浦',
    'Emi': '江見', 'Futomi': '太海',

    #総武本線
    'ShinNihombashi': '新日本橋', 'Bakurocho': '馬喰町',
    'HigashiChiba': '東千葉', 'Tsuga': '都賀', 'Yotsukaido': '四街道', 'Monoi': '物井',
    'Sakura': '佐倉', 'MinamiShisui': '南酒々井', 'Enokido': '榎戸', 'Yachimata': '八街',
    'Hyuga': '日向', 'Naruto': '成東', 'Matsuo': '松尾', 'Yokoshiba': '横芝', 'Iigura': '飯倉',
    'Yokaichiba': '八日市場', 'Higata': '干潟', 'Asahi': '旭', 'Iioka': '飯岡', 'Kurahashi': '倉橋',
    'Saruta': '猿田', 'Matsugishi': '松岸', 'Choshi': '銚子',

    #東金線
    'Fukutawara': '福俵', 'Togane': '東金', 'Gumyo': '求名',

    #京葉線
    'Hatchobori': '八丁堀', 'Etchujima': '越中島', 'Shiomi': '潮見', 
    'KasaiRinkaiPark': '葛西臨海公園',
    'Maihama': '舞浜', 'ShinUrayasu': '新浦安', 'Ichikawashiohama': '市川塩浜', 
    'Futamatashinmachi': '二俣新町', 'MinamiFunabashi': '南船橋',
    'ShinNarashino': '新習志野', 'Kaihimmakuhari': '海浜幕張', 'Kemigawahama': '検見川浜',
    'Inagekaigan': '稲毛海岸', 'Chibaminato': '千葉みなと', 'Soga': '蘇我', 

    #武蔵野線
    'FubashiHoten': '船橋法典', 'Ichikawaono': '市川大野', 'HigashiMatsudo': '東松戸',
    'ShinYabashira': '新八柱', 'ShimMatsudo': '新松戸', 'MinamiNagareyama': '南流山',
    'Misato': '三郷', 'ShimMisato': '新三郷', 'Yoshikawa': '吉川', 'YoshikawaMinami': '吉川美南',
    'KoshigayaLakeTown': '越谷レイクタウン',
    'MinamiKoshigaya': '南越谷', 'HigashiKawaguchi': '東川口', 'HigashiUrawa': '東浦和',
    'MinamiUrawa': '南浦和', 'Musashiurawa': '武蔵浦和', 'Nishiurawa': '西浦和',
    'KitaAsaka': '北朝霞', 'Niiza': '新座', 'HigashiTokorozawa': '東所沢',
    'ShinAkitsu': '新秋津', 'ShinKodaira': '新小平', 'NishiKokubunji': '西国分寺',
    'KitaFuchu': '北府中',

    #京浜東北根岸線
    'Omiya': '大宮', 'SaitamaShintoshin': 'さいたま新都心', 'Yono': '与野', 'KitaUrawa': '北浦和', 
    'Urawa': '浦和', 'MinamiUrawa': '南浦和', 'Warabi': '蕨', 'NishiKawaguchi': '西川口', 
    'Kawaguchi': '川口', 'Akabane': '赤羽', 'HigashiJujo': '東十条', 'Oji': '王子', 
    'KamiNakazato': '上中里', 'Oimachi': '大井町', 'Omori': '大森', 'Kamata': '蒲田', 
    'Kawasaki': '川崎', 
    'Tsurumi': '鶴見', 'ShinKoyasu': '新子安', 'HigashiKanagawa': '東神奈川', 'Yokohama': '横浜', 
    'Sakuragicho': '桜木町', 'Kannai': '関内', 'Ishikawacho': '石川町', 'Yamate': '山手', 
    'Negishi': '根岸', 'Isogo': '磯子', 'ShinSugita': '新杉田', 'Yokodai': '洋光台', 
    'Konandai': '港南台', 'Hongodai': '本郷台', 'Ofuna': '大船',

    #中央・総武線各駅停車
    'HigashiNakano': '東中野', 'Okubo': '大久保', 'Yoyogi': '代々木', 'Sendagaya': '千駄ケ谷',
    'Shinanomachi': '信濃町', 'Ichigaya': '市ケ谷', 'Iidabashi': '飯田橋', 'Suidobashi': '水道橋', 
    'Akihabara': '秋葉原', 'Asakusabashi': '浅草橋', 'Ryogoku': '両国', 'Kinshicho': '錦糸町', 
    'Kameido': '亀戸', 'Hirai': '平井', 
    'ShinKoiwa': '新小岩', 'Koiwa': '小岩', 'Ichikawa': '市川', 'Motoyawata': '本八幡', 
    'ShimosaNakayama': '下総中山', 'Nishi-Funabashi': '西船橋', 'Funabashi': '船橋', 
    'HigashiFunabashi': '東船橋', 'Tsudanuma': '津田沼', 'MakuhariHongo': '幕張本郷', 
    'Makuhari': '幕張', 'ShinKemigawa': '新検見川', 'Inage': '稲毛', 'NishiChiba': '西千葉', 
    'Chiba': '千葉',

    # --- [追加] 東京メトロ東西線・東葉高速線 ---
    'Nakano': '中野', 'Ochiai': '落合', 'Takadanobaba': '高田馬場', 'Waseda': '早稲田', 
    'Kagurazaka': '神楽坂', 'Iidabashi': '飯田橋', 'Kudanshita': '九段下', 
    'Takebashi': '竹橋', 'Otemachi': '大手町', 'Nihombashi': '日本橋', 'Kayabacho': '茅場町', 
    'MonzenNakacho': '門前仲町', 'Kiba': '木場', 'Toyocho': '東陽町', 
    'MinamiSunamachi': '南砂町', 'NishiKasai': '西葛西', 'Kasai': '葛西', 
    'Urayasu': '浦安', 'MinamiGyotoku': '南行徳', 'Gyotoku': '行徳', 'Myoden': '妙典', 
    'BarakiNakayama': '原木中山', 'NishiFunabashi': '西船橋', 
    'HigashiKaijin': '東海神', 'Hasama': '飯山満', 'KitaNarashino': '北習志野', 
    'FunabashiNichidaimae': '船橋日大前', 'YachiyoMidorigaoka': '八千代緑が丘', 
    'YachiyoChuo': '八千代中央', 'Murakami': '村上', 'ToyoKatsutadai': '東葉勝田台',

    #南武線
    'Tachikawa': '立川', 'NishiKunitachi': '西国立', 'Yagawa': '矢川', 'Yaho': '谷保', 
    'Nishifu': '西府', 'Bubaigawara': '分倍河原', 'Fuchuhommachi': '府中本町', 
    'MinamiTama': '南多摩', 'Inaginaganuma': '稲城長沼', 'Yanokuchi': '矢野口', 
    'Inadazutsumi': '稲田堤', 'Nakanoshima': '中野島', 'Noborito': '登戸', 'Shukugawara': '宿河原', 
    'Kuji': '久地', 'MusashiMizonokuchi': '武蔵溝ノ口', 'MusashiShinjo': '武蔵新城', 
    'MusashiNakahara': '武蔵中原', 'Musashi-Kosugi': '武蔵小杉', 'Mukaigawara': '向河原', 
    'Hirama': '平間', 'Kashimada': '鹿島田', 'Yako': '矢向', 'Shitte': '尻手', 
    'Kawasaki': '川崎',

    #横浜線
    'Hachioji': '八王子', 'Katakura': '片倉', 'HachiojiMinamino': '八王子みなみ野', 
    'Aihara': '相原', 'Hashimoto': '橋本', 'Sagamihara': '相模原', 'Yabe': '矢部', 
    'Fuchinobe': '淵野辺', 'Kobeshi': '古淵', 'Machida': '町田', 'Naruse': '成瀬', 
    'Nagatsuta': '長津田', 'Tokaichiba': '十日市場', 'Nakayama': '中山', 'Kamoi': '鴨居', 
    'Kozukue': '小机', 'ShinYokohama': '新横浜', 'Kikuna': '菊名', 'Oguchi': '大口', 
    'HigashiKanagawa': '東神奈川',

    # 両毛・上越線 (北急十日町～高崎)
    'Tokamachi': '十日町', 'EchigoYuzawa': '越後湯沢', 'Doai': '土合', 'Minakami': '水上',
    'Numazawa': '沼田', 'Shibukawa': '渋川', 'Maebashi': '前橋', 'ShinMaebashi': '新前橋', 
    'Ino': '井野', 'Takasakitonyamachi': '高崎問屋町', 'Takasaki': '高崎',

    # 高崎線 (倉賀野～宮原)
    'Kuragano': '倉賀野', 'Shinmachi': '新町', 'Jimbohara': '神保原', 'Honjo': '本庄', 
    'Okabe': '岡部', 'Fukaya': '深谷', 'Kagohara': '籠原', 'Kumagaya': '熊谷', 'Gyoda': '行田', 
    'Fukiage': '吹上', 'KitaKonosu': '北鴻巣', 'Konosu': '鴻巣', 'Kitamoto': '北本', 
    'Okegawa': '桶川', 'KitaAgeo': '北上尾', 'Ageo': '上尾', 'Miyahara': '宮原',

    # 宇都宮線 (宇都宮～大宮)
    'Utsunomiya': '宇都宮', 'Suzumenomiya': '雀宮', 'Ishibashi': '石橋', 'Jichiidai': '自治医大', 
    'Koganei': '小金井', 'Nogi': '野木', 'Mamada': '間々田', 'Oyama': '小山', 'Koga': '古河', 
    'Kurihashi': '栗橋', 'HigashiWashinomiya': '東鷲宮',
    'Kuki': '久喜', 'Shiraoka': '白岡', 'Hasuda': '蓮田', 'HigashiOmiya': '東大宮', 'Toro': '土呂',
    
    #宇都宮線
    'Okamoto': '岡本', 'Hoshakuji': '宝積寺', 'Ujiie': '氏家', 'Kamasusaka': '蒲須坂',
    'Kataoka': '片岡', 'Yaita': '矢板', 'Nozaki': '野崎', 'NishiNasuno': '西那須野',
    'Nasushiobara': '那須塩原', 'Kuroiso': '黒磯',

    #烏山線
    'Karasuyama': '烏山', 'Ogane': '大金', 'Konoyama': '鴻野山', 'Niita': '仁井田',
    'ShimotsukeHanaoka': '下野花岡', 

    #日光線
    'Tsuruta': '鶴田', 'Kanuma': '鹿沼', 'Fubasami': '文挟', 'ShimotsukeOsawa': '下野大沢',
    'Imaichi': '今市', 'Nikko': '日光',

    #烏山線
    'ShimotsukeHanaoka': '下野花岡', 'Niita': '仁井田', 'Konoyama': '鴻野山',
    'Ogane': '大金', 'Karasuyama': '烏山',

    # 湘南新宿ライン・横須賀線 (大宮～久里浜)
    'NishiOi': '西大井', 'MusashiKosugi': '武蔵小杉', 'ShinKawasaki': '新川崎', 'Yokohama': '横浜', 
    'Hodogaya': '保土ケ谷', 'HigashiTotsuka': '東戸塚', 'Totsuka': '戸塚', 'Ofuna': '大船', 
    'KitaKamakura': '北鎌倉', 'Kamakura': '鎌倉', 'Zushi': '逗子', 'HigashiZushi': '東逗子', 
    'Taura': '田浦', 'Yokosuka': '横須賀', 'Kinugasa': '衣笠', 'Kurihama': '久里浜',

    # 東海道線 (横浜～沼津、以遠主要駅)
    'Fujisawa': '藤沢', 'Tsujido': '辻堂', 'Chigasaki': '茅ヶ崎', 'Hiratsuka': '平塚', 'Oiso': '大磯',
    'Ninomiya': '二宮', 'Kozu': '国府津', 'Kamonomiya': '鴨宮', 'Odawara': '小田原',
    'Hayakawa': '早川', 'Nebukawa': '根府川', 'Manazuru': '真鶴', 'Yugawara': '湯河原', 
    'Atami': '熱海', 'Kannami': '函南', 'Mishima': '三島', 'Numazu': '沼津', 'Shizuoka': '静岡',
    'Hamamatsu': '浜松', 'Toyohashi': '豊橋', 'Nagoya': '名古屋', 'Gifu': '岐阜', 'Ogaki': '大垣', 
    'Maibara': '米原', 'Osaka': '大阪', 'ShinOsaka': '新大阪', 'Himeji': '姫路', 'Okayama': '岡山', 
    'Takamatsu': '高松', 'Kotohira': '琴平', 'Izumoshi': '出雲市',

    # 伊東線・伊豆箱根鉄道(主要駅)
    'Kinomiya': '来宮', 'IzuTaga': '伊豆多賀', 'Ajiro': '網代', 'Usami': '宇佐美', 'Ito': '伊東',
    'IzukyuShimoda': '伊豆急下田','IzuKogen': '伊豆高原', 'Daiba': '大場','Shuzenji': '修善寺',

    #常磐線 (上野～大津港、以遠仙台まで主要駅)
    'Ueno': '上野', 'Nippori': '日暮里', 'Mikawashima': '三河島', 'MinamiSenju': '南千住',
    'KitaSenju': '北千住', 'Ayase': '綾瀬', 'Kameari': '亀有', 'Kanamachi':'金町',
    'Matsudo': '松戸', 'KitaMatsudo': '北松戸', 'Mabashi': '馬橋', 'ShinMatsudo': '新松戸',
    'KitaKogane': '北小金', 'Kashiwa': '柏', 'KitaKashiwa': '北柏', 'Abiko': '我孫子',
    'Tennodai': '天王台', 'Toride': '取手', 'Fujishiro': '藤代', 'Ryugasakishi': '龍ケ崎市',
    'Ushiku': '牛久', 'Hitachinoushiku': 'ひたち野うしく', 'Arakawaoki': '荒川沖',
    'Tsuchiura': '土浦', 'Kandatsu': '神立', 'Takahama': '高浜', 'Ishioka': '石岡',
    'Hatori': '羽鳥', 'Iwama': '岩間', 'Tomobe': '友部', 'Uchihara': '内原', 'Akatsuka': '赤塚',
    'Kairakuen': '偕楽園', 'Mito': '水戸', 'Katsuta': '勝田', 'Sawa': '佐和',
    'Tokai': '東海', 'Omika': '大甕', 'HitachiTaga': '常陸多賀', 'Hitachi': '日立',
    'Ogitsu': '小木津', 'Ju-O': '十王', 'Takahagi': '高萩', 'MinamiNakago': '南中郷',
    'Isohara': '磯原', 'Otsuko': '大津港',
    'Nakoso': '勿来', 'Ueda': '植田', 'Izumi': '泉', 'Yumoto': '湯本', 'Iwaki': 'いわき',
    'Hirono': '広野', 'Tomioka': '富岡', 'Okuma': '大熊', 'Futaba': '双葉', 'Namie': '浪江',
    'Odaka': '小高', 'Haranomachi': '原ノ町', 'Soma': '相馬', 'Shinchi': '新地',
    'Watari': '亘理', 'Iwanuma': '岩沼', 'Natori': '名取', 'MinamiSendai': '南仙台',
    'Nagame': '長町', 'Sendai': '仙台',

    #りんかい線・埼京線・川越線(新木場～川越)
    'Kawagoe': '川越', 'NishiKawagoe': '西川越', 'Matoba': '的場', 'Kasahata': '笠幡',
    'MusashiTakahagi': '武蔵高萩', 'Komagawa': '高麗川', 'MinamiFuruya': '南古谷',
    'NishiOmiya' : '西大宮',
    'Sashiogi': '指扇', 'Nisshin': '日進', 'Omiya': '大宮', 'KitaYono': '北与野',
    'YonoHommachi': '与野本町', 'MinamiYono': '南与野', 'NakaUrawa': '中浦和',
    'MusashiUrawa': '武蔵浦和', 'KitaToda': '北戸田', 'Toda': '戸田', 'TodaKoen': '戸田公園',
    'UkimaFunado': '浮間舟渡', 'KitaAkabane': '北赤羽', 'Akabane': '赤羽', 'Jujo': '十条',
    'Itabashi': '板橋', 'Oimachi': '大井町', 'ShinagawaSeaside': '品川シーサイド',
    'TennozuIsle': '天王洲アイル', 'TokyoTeleport': '東京テレポート',
    'KokusaiTenjijo': '国際展示場', 'Shinonome': '東雲', 'ShinKiba': '新木場',
    
    #相鉄線
    'Yokohama': '横浜', 'Hodogaya': '保土ケ谷', 'Nishiya': '西谷',
    'Futamatagawa': '二俣川', 'Seya': '瀬谷',
    'Hazawayokohamakokudai': '羽沢横浜国大',

    #八高・川越線(川越～八王子)
    'Hachioji': '八王子', 'KitaHachioji': '北八王子', 'Komiya': '小宮', 
    'HigashiFussa': '東福生', 'Hakonegasaki': '箱根ケ崎', 'HigashiHanno': '東飯能',
    'Komagawa': '高麗川', 'MusashiTakahagi': '武蔵高萩', 'Kasahata': '笠幡', 'Matoba': '的場',
    'NishiKawagoe': '西川越', 

    #千代田線・小田急線主要駅
    'HakoneYumoto': '箱根湯本', 'ShinMatsuda': '新松田', 'Hadano': '秦野', 'Isehara': '伊勢原', 
    'HonAtsugi':'本厚木', 'Ebina': '海老名', 'SagamiOno': '相模大野', 'ShinYurigaoka': '新百合ヶ丘', 
    'Karakiida': '唐木田', 'MukogaokaYuen': '向ケ丘遊園', 'SeijogakuenMae': '成城学園前', 
    'YoyogiUehara': '代々木上原', 'YoyogiKoen': '代々木公園', 'MeijiJingumae': '明治神宮前',
    'Omotesando': '表参道', 'Kasumigaseki': '霞ケ関', 'Otemachi': '大手町', 'Yushima': '湯島',  

    #成田線
    'NaritaAirportTerminal1': '成田空港', 'Narita': '成田'

}

TRAIN_TYPE_NAMES = {
    'odpt.TrainType:JR-East.Local': '各停',
    'odpt.TrainType:JR-East.Rapid': '快速',
    'odpt.TrainType:JR-East.ChuoSpecialRapid': '中央特快',
    'odpt.TrainType:JR-East.OmeSpecialRapid': '青梅特快',
    'odpt.TrainType:JR-East.CommuterRapid': '通勤快速',
    'odpt.TrainType:JR-East.CommuterSpecialRapid': '通勤特快',
    'odpt.TrainType:JR-East.SpecialRapid': '特別快速',
    'odpt.TrainType:JR-East.LimitedExpress': '特急',
    # 他の種別も必要に応じて追加可能
}

KEIHIN_TOHOKU_STATIONS = [
    '大宮', 'さいたま新都心', '与野', '北浦和', '浦和', '南浦和', '蕨', '西川口',
    '川口', '赤羽', '東十条', '王子', '上中里', '田端', '西日暮里', '日暮里',
    '鶯谷', '上野', '御徒町', '秋葉原', '神田', '東京', '有楽町', '新橋',
    '浜松町', # ← ここが境界
    '田町', '高輪ゲートウェイ', '品川', '大井町', '大森', '蒲田',
    '川崎', '鶴見', '新子安', '東神奈川', '横浜', '桜木町', '関内', '石川町',
    '山手', '根岸', '磯子', '新杉田', '洋光台', '港南台', '本郷台', '大船'
]

JR_LINES_TO_MONITOR = [
    {
        "id": "odpt.Railway:JR-East.Yamanote",
        "name": "山手線",
        "regular_trips": {
            ('odpt.RailDirection:InnerLoop', 'Ikebukuro'),
            ('odpt.RailDirection:InnerLoop', 'Osaki'),
            ('odpt.RailDirection:OuterLoop', 'Ikebukuro'),
            ('odpt.RailDirection:OuterLoop', 'Osaki'),
            ('odpt.RailDirection:OuterLoop', 'Shinagawa'),
        }
    },
    { # ▼▼▼ 2. 中央線快速を監視対象に追加 ▼▼▼
        "id": "odpt.Railway:JR-East.ChuoRapid",
        "name": "中央快速線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.Rapid', 'Mitaka'),
            ('odpt.TrainType:JR-East.Rapid', 'MusashiKoganei'),
            ('odpt.TrainType:JR-East.Rapid', 'Kokubunji'),
            ('odpt.TrainType:JR-East.Rapid', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Ome'),
            ('odpt.TrainType:JR-East.Rapid', 'Toyoda'),
            ('odpt.TrainType:JR-East.Rapid', 'Hachioji'),
            ('odpt.TrainType:JR-East.Rapid', 'Takao'),
            ('odpt.TrainType:JR-East.Rapid', 'Otsuki'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Takao'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Otsuki'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Kawaguchiko'),        
            ('odpt.TrainType:JR-East.OmeSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.OmeSpecialRapid', 'Ome'),       
            ('odpt.TrainType:JR-East.CommuterRapid', 'Takao'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Ome'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Otsuki'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Kawaguchiko'),
            ('odpt.TrainType:JR-East.CommuterSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Ome'),
        }
    },
    { # 他路線
        "id": "odpt.Railway:JR-East.ChuoSobuLocal",
        "name": "中央総武線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Mitaka'),
            ('odpt.TrainType:JR-East.Local', 'Nakano'),
            ('odpt.TrainType:JR-East.Local', 'Ochanomizu'),
            ('odpt.TrainType:JR-East.Local', 'NishiFunabashi'),
            ('odpt.TrainType:JR-East.Local', 'Tsudanuma'),
            ('odpt.TrainType:JR-East.Local', 'Chiba'),
            ('odpt.TrainType:JR-East.Local', 'Toyocho'),
            ('odpt.TrainType:JR-East.Local', 'Myoden'),
            ('odpt.TrainType:JR-East.Local', 'ToyoKatsutadai'),
            ('odpt.TrainType:JR-East.Rapid', 'NishiFunabashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Tsudanuma'),
            ('odpt.TrainType:JR-East.Rapid', 'ToyoKatsutadai'),
            ('odpt.TrainType:JR-East.Rapid', 'Nakano'),
            ('odpt.TrainType:JR-East.Rapid', 'Mitaka'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Nakano'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Mitaka'),
        }
    },
    { # 京浜東北根岸線
        "id": "odpt.Railway:JR-East.KeihinTohokuNegishi",
        "name": "京浜東北/根岸線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Hachioji'),
            ('odpt.TrainType:JR-East.Local', 'Hashimoto'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'MinamiUrawa'),
            ('odpt.TrainType:JR-East.Local', 'Akabane'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Kamata'),
            ('odpt.TrainType:JR-East.Local', 'Tsurumi'),
            ('odpt.TrainType:JR-East.Local', 'HigashiKanagawa'),
            ('odpt.TrainType:JR-East.Local', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Local', 'Isogo'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Rapid', 'Omiya'),
            ('odpt.TrainType:JR-East.Rapid', 'MinamiUrawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Kamata'),
            ('odpt.TrainType:JR-East.Rapid', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Rapid', 'Isogo'),
            ('odpt.TrainType:JR-East.Rapid', 'Ofuna'),
            ('odpt.TrainType:JR-East.Rapid', 'Hachioji'),
        }
    },
    { # 南武線
        "id": "odpt.Railway:JR-East.Nambu",
        "name": "南武線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Local', 'Inaginaganuma'),
            ('odpt.TrainType:JR-East.Local', 'Noborito'),
            ('odpt.TrainType:JR-East.Local', 'MusashiNakahara'),
            ('odpt.TrainType:JR-East.Local', 'MusashiShinjo'),
            ('odpt.TrainType:JR-East.Local', 'MusashiMizonokuchi'),
            ('odpt.TrainType:JR-East.Local', 'Kawasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Inaginaganuma'),
            ('odpt.TrainType:JR-East.Rapid', 'Kawasaki'),
        }
    },
    { # 横浜線
        "id": "odpt.Railway:JR-East.Yokohama",
        "name": "横浜線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Hachioji'),
            ('odpt.TrainType:JR-East.Local', 'Hashimoto'),
            ('odpt.TrainType:JR-East.Local', 'Machida'),
            ('odpt.TrainType:JR-East.Local', 'HigashiKanagawa'),
            ('odpt.TrainType:JR-East.Local', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Local', 'Isogo'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Rapid', 'Hachioji'),
            ('odpt.TrainType:JR-East.Rapid', 'Sakuragicho'),
            ('odpt.TrainType:JR-East.Rapid', 'Isogo'),
            ('odpt.TrainType:JR-East.Rapid', 'Ofuna'),
        }
    },
    { # 常磐快速線
        "id": "odpt.Railway:JR-East.JobanRapid",
        "name": "常磐快速線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.Local', 'Mito'),
            ('odpt.TrainType:JR-East.Local', 'Katsuta'),
            ('odpt.TrainType:JR-East.Local', 'Takahagi'),
            ('odpt.TrainType:JR-East.Rapid', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.Rapid', 'Mito'),
            ('odpt.TrainType:JR-East.Rapid', 'Katsuta'),
            ('odpt.TrainType:JR-East.Rapid', 'Takahagi'),
            ('odpt.TrainType:JR-East.Rapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Matsudo'),
            ('odpt.TrainType:JR-East.Rapid', 'Abiko'),
            ('odpt.TrainType:JR-East.Rapid', 'Narita'),
            ('odpt.TrainType:JR-East.Rapid', 'Toride'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinagawa'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Iwaki'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Sendai'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Katsuta'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Takahagi'),
        }
    },
    { # 常磐線取手以北
        "id": "odpt.Railway:JR-East.Joban",
        "name": "常磐線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Abiko'),
            ('odpt.TrainType:JR-East.Local', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.Local', 'Mito'),
            ('odpt.TrainType:JR-East.Local', 'Katsuta'),
            ('odpt.TrainType:JR-East.Local', 'Takahagi'),
            ('odpt.TrainType:JR-East.Local', 'Iwaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Abiko'),
            ('odpt.TrainType:JR-East.Rapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinagawa'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Iwaki'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Sendai'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Katsuta'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Takahagi'),
        }
    },
    { # 武蔵野線
        "id": "odpt.Railway:JR-East.Musashino",
        "name": "武蔵野線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Fuchuhommachi'),
            ('odpt.TrainType:JR-East.Local', 'HigashiTokorozawa'),
            ('odpt.TrainType:JR-East.Local', 'Yoshikawaminami'),
            ('odpt.TrainType:JR-East.Local', 'NishiFunabashi'),
            ('odpt.TrainType:JR-East.Local', 'MinamiFunabashi'),
            ('odpt.TrainType:JR-East.Local', 'ShinNarashino'),
            ('odpt.TrainType:JR-East.Local', 'Kaihimmakuhari'),
            ('odpt.TrainType:JR-East.Local', 'MinamiKoshigaya'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Hachioji'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
        }
    },
    { # 中央線高尾以西
        "id": "odpt.Railway:JR-East.Chuo",
        "name": "中央本線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Local', 'Takao'),
            ('odpt.TrainType:JR-East.Local', 'Otsuki'),
            ('odpt.TrainType:JR-East.Local', 'Kawaguchiko'),
            ('odpt.TrainType:JR-East.Local', 'Kofu'),
            ('odpt.TrainType:JR-East.Local', 'Nirasaki'),
            ('odpt.TrainType:JR-East.Local', 'Kobuchizawa'),
            ('odpt.TrainType:JR-East.Local', 'Enzan'),
            ('odpt.TrainType:JR-East.Local', 'Matsumoto'),
            ('odpt.TrainType:JR-East.Local', 'Nagano'),
            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.ChuoSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.CommuterSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Kofu'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Matsumoto'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Hakuba'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Tokyo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Chiba'),        
        }
    },
    { # 湘南新宿ライン
        "id": "odpt.Railway:JR-East.ShonanShinjuku",
        "name": "湘南新宿ﾗｲﾝ",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Local', 'Zushi'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Rapid', 'Kozu'),
            ('odpt.TrainType:JR-East.Rapid', 'Odawara'),
            ('odpt.TrainType:JR-East.Rapid', 'Zushi'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ohuna'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Odawara'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'TobuNikko'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'KinugawaOnsen'),        
        }
    },
    { # 高崎線
        "id": "odpt.Railway:JR-East.Takasaki",
        "name": "高崎線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'ShimMaebashi'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.Rapid', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Rapid', 'Kozu'),
            ('odpt.TrainType:JR-East.Rapid', 'Odawara'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'), 
            ('odpt.TrainType:JR-East.LimitedExpress', 'Naganoharakusatsuguchi'),    
            ('odpt.TrainType:JR-East.LimitedExpress', 'Takasaki'),    
            ('odpt.TrainType:JR-East.LimitedExpress', 'Konosu'),    
            ('odpt.TrainType:JR-East.LimitedExpress', 'Honjo'),    
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ueno'),    
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),    
        }
    },
    { # 宇都宮線
        "id": "odpt.Railway:JR-East.Utsunomiya",
        "name": "宇都宮線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Nikko'),
            ('odpt.TrainType:JR-East.Local', 'Kuroiso'),
            ('odpt.TrainType:JR-East.Local', 'Karasuyama'),
            ('odpt.TrainType:JR-East.Rapid', 'Ueno'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'TobuNikko'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'KinugawaOnsen'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Local', 'Zushi'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Zushi'),    
        }
    },
    {
        "id": "odpt.Railway:JR-East.Itsukaichi",
        "name": "五日市線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'MusashiItsukaichi'),
            ('odpt.TrainType:JR-East.Local', 'Haijima'),
            ('odpt.TrainType:JR-East.Local', 'Tachikawa'),
        }
    },
    {
        "id": "odpt.Railway:JR-East.Ome",
        "name": "青梅線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'OkuTama'),
            ('odpt.TrainType:JR-East.Local', 'Ome'),
            ('odpt.TrainType:JR-East.Local', 'Kabe'),
            ('odpt.TrainType:JR-East.Local', 'MusashiItsukaichi'),
            ('odpt.TrainType:JR-East.Local', 'Haijima'),
            ('odpt.TrainType:JR-East.Local', 'Tachikawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Mitaka'),
            ('odpt.TrainType:JR-East.Rapid', 'MusashiKoganei'),
            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.OmeSpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Ome'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'OkuTama'),
            ('odpt.TrainType:JR-East.CommuterSpecialRapid', 'Tokyo'),
        }
    },
    {
        "id": "odpt.Railway:JR-East.Tokaido",
        "name": "東海道線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Ito'),
            ('odpt.TrainType:JR-East.Local', 'Numazu'),
            ('odpt.TrainType:JR-East.Local', 'Atami'),
            ('odpt.TrainType:JR-East.Local', 'Odawara'),
            ('odpt.TrainType:JR-East.Local', 'Kozu'),
            ('odpt.TrainType:JR-East.Local', 'Hiratsuka'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Ueno'),
            ('odpt.TrainType:JR-East.Local', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.Local', 'Mito'),
            ('odpt.TrainType:JR-East.Local', 'Katsuta'),
            ('odpt.TrainType:JR-East.Local', 'Takahagi'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Local', 'Kagohara'),
            ('odpt.TrainType:JR-East.Local', 'Takasaki'),
            ('odpt.TrainType:JR-East.Local', 'ShimMaebashi'),
            ('odpt.TrainType:JR-East.Local', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Matsudo'),
            ('odpt.TrainType:JR-East.Rapid', 'Toride'),
            ('odpt.TrainType:JR-East.Rapid', 'Narita'),
            ('odpt.TrainType:JR-East.Rapid', 'Maebashi'),
            ('odpt.TrainType:JR-East.Rapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.Rapid', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Kagohara'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Tsuchiura'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Takasaki'),
            ('odpt.TrainType:JR-East.SpecialRapid', 'Odawara'),
        }
    },
    {
        "id": "odpt.Railway:JR-East.SobuRapid",
        "name": "総武快速線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Rapid', 'Kimitsu'),
            ('odpt.TrainType:JR-East.Rapid', 'Sakura'),
            ('odpt.TrainType:JR-East.Rapid', 'KazusaIchinomiya'),
            ('odpt.TrainType:JR-East.Rapid', 'Narita'),
            ('odpt.TrainType:JR-East.Rapid', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:JR-East.Rapid', 'Naruto'),
            ('odpt.TrainType:JR-East.Rapid', 'Chiba'),
            ('odpt.TrainType:JR-East.Rapid', 'Tsudanuma'),
            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.Rapid', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Rapid', 'Ofuna'),
            ('odpt.TrainType:JR-East.Rapid', 'Yokosuka'),
            ('odpt.TrainType:JR-East.Rapid', 'Zushi'),
            ('odpt.TrainType:JR-East.Rapid', 'Kurihama'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Shinjuku'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ofuna'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Sakura'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Naruto'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Choshi'),

        }
    },
    {
        "id": "odpt.Railway:JR-East.Keiyo",
        "name": "京葉線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'NishiFunabashi'),
            ('odpt.TrainType:JR-East.Local', 'MinamiFunabashi'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'HigashiTokorozawa'),
            ('odpt.TrainType:JR-East.Local', 'Fuchuhommachi'),
            ('odpt.TrainType:JR-East.Local', 'ShinNarashino'),
            ('odpt.TrainType:JR-East.Local', 'Kaihimmakuhari'),
            ('odpt.TrainType:JR-East.Local', 'Soga'),
            ('odpt.TrainType:JR-East.Local', 'Honda'),
            ('odpt.TrainType:JR-East.Local', 'KazusaIchinomiya'),
            ('odpt.TrainType:JR-East.Local', 'Kimitsu'),
            ('odpt.TrainType:JR-East.Rapid', 'Tokyo'),
            ('odpt.TrainType:JR-East.Rapid', 'Soga'),
            ('odpt.TrainType:JR-East.Rapid', 'Kimitsu'),
            ('odpt.TrainType:JR-East.Rapid', 'KazusaIchinomiya'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Tokyo'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'KazusaIchinomiya'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Awakamogawa'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Katsuura'),

        }
    },
    {# 埼京線
        "id": "odpt.Railway:JR-East.SaikyoKawagoe",
            "name": "埼京/川越線",
            "regular_trips": { 
            ('odpt.TrainType:JR-East.Local', 'Hachioji'),
            ('odpt.TrainType:JR-East.Local', 'Haijima'),
            ('odpt.TrainType:JR-East.Local', 'Komagawa'),
            ('odpt.TrainType:JR-East.Local', 'Kawagoe'),
            ('odpt.TrainType:JR-East.Local', 'Omiya'),
            ('odpt.TrainType:JR-East.Local', 'MusashiUrawa'),
            ('odpt.TrainType:JR-East.Local', 'Akabane'),
            ('odpt.TrainType:JR-East.Local', 'Ikebukuro'),
            ('odpt.TrainType:JR-East.Local', 'Shinjuku'),
            ('odpt.TrainType:JR-East.Local', 'Osaki'),
            ('odpt.TrainType:JR-East.Local', 'ShinKiba'),
            ('odpt.TrainType:JR-East.Local', 'Ebina'),
            ('odpt.TrainType:JR-East.Rapid', 'Kawagoe'),
            ('odpt.TrainType:JR-East.Rapid', 'ShinKiba'),
            ('odpt.TrainType:JR-East.Rapid', 'Ebina'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Kawagoe'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'Shinjuku'),
            ('odpt.TrainType:JR-East.CommuterRapid', 'ShinKiba'), 
            }
    },
    { # 相鉄直通線
        "id": "odpt.Railway:JR-East.SotetsuDirect",
            "name": "相鉄直通線",
            "regular_trips": {
                ('odpt.TrainType:JR-East.Local', 'Ebina'),
                ('odpt.TrainType:JR-East.Local', 'Shinjuku'),
                ('odpt.TrainType:JR-East.Local', 'Ikebukuro'),
                ('odpt.TrainType:JR-East.Local', 'Akabane'),
                ('odpt.TrainType:JR-East.Local', 'MusashiUrawa'),
                ('odpt.TrainType:JR-East.Local', 'Omiya'),
                ('odpt.TrainType:JR-East.Local', 'Kawagoe'),
                ('odpt.TrainType:JR-East.Rapid', 'Kawagoe'),
                ('odpt.TrainType:JR-East.CommuterRapid', 'Kawagoe'),
            }
    },
    { # 川越線(川越～高麗川)
        "id": "odpt.Railway:JR-East.Kawagoe",
        "name": "川越線",
        "regular_trips": {
            ('odpt.TrainType:JR-East.Local', 'Kawagoe'),  
            ('odpt.TrainType:JR-East.Local', 'Komagawa'),
            ('odpt.TrainType:JR-East.Local', 'Haijima'),
            ('odpt.TrainType:JR-East.Local', 'Hachioji'), 
            }
    },
    { #常磐緩行線
        "id": "odpt.Railway:JR-East.JobanLocal",
        "name": "常磐緩行線",
        "regular_trips": {
           ('odpt.TrainType:JR-East.Local', 'YoyogiUehara'),
           ('odpt.TrainType:JR-East.Local', 'Karakida'),
           ('odpt.TrainType:JR-East.Local', 'MukogaokaYuen'),
           ('odpt.TrainType:JR-East.Local', 'SeijogakuenMae'),
           ('odpt.TrainType:JR-East.Local', 'KitaSenju'),
           ('odpt.TrainType:JR-East.Local', 'Isehara'),
           ('odpt.TrainType:JR-East.Local', 'Kasumigaseki'),
           ('odpt.TrainType:JR-East.Local', 'MeijiJingumae'),
           ('odpt.TrainType:JR-East.Local', 'HonAtsugi'),
           ('odpt.TrainType:JR-East.Local', 'Matsudo'),
           ('odpt.TrainType:JR-East.Local', 'Kashiwa'),
           ('odpt.TrainType:JR-East.Local', 'Abiko'),
           ('odpt.TrainType:JR-East.Local', 'Toride'),
        }
    },
    { #横須賀線
        "id": "odpt.Railway:JR-East.Yokosuka",
        "name": "横須賀線",
        "regular_trips": {
           ('odpt.TrainType:JR-East.Local', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:JR-East.Local', 'Naruto'),
            ('odpt.TrainType:JR-East.Local', 'Kimitsu'),
            ('odpt.TrainType:JR-East.Local', 'Sakura'),
            ('odpt.TrainType:JR-East.Local', 'KazusaIchinomiya'),
            ('odpt.TrainType:JR-East.Local', 'Narita'),
            ('odpt.TrainType:JR-East.Local', 'Chiba'),
            ('odpt.TrainType:JR-East.Local', 'Tsudanuma'),
            ('odpt.TrainType:JR-East.Local', 'Tokyo'),
            ('odpt.TrainType:JR-East.Local', 'Shinagawa'),
            ('odpt.TrainType:JR-East.Local', 'Ofuna'),
            ('odpt.TrainType:JR-East.Local', 'Kurihama'),
            ('odpt.TrainType:JR-East.Local', 'Yokosuka'),
            ('odpt.TrainType:JR-East.Local', 'Zushi'),
            ('odpt.TrainType:JR-East.Local', 'Koga'),
            ('odpt.TrainType:JR-East.Local', 'Koganei'),
            ('odpt.TrainType:JR-East.Local', 'Utsunomiya'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'Ofuna'),
            ('odpt.TrainType:JR-East.LimitedExpress', 'NaritaAirportTerminal1'),
        }
    },
]

HEBIKUBO_TARGET_LINES = {
    "odpt.Railway:JR-East.SaikyoKawagoe",
    "odpt.Railway:JR-East.ShonanShinjuku",
    "odpt.Railway:JR-East.SotetsuDirect", 
}

notified_trains = set()

def fetch_train_data(line_config):
    try:
        params = {"odpt:railway": line_config["id"], "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"--- [FETCH] {line_config['name']}のデータ取得中にエラー発生: {e}", flush=True)
        return None

def _is_yamanote_line_train_irregular(train, line_config):
    """山手線の列車を専門的に判定する"""
    direction_id = train.get("odpt:railDirection")
    dest_station_en = train.get("odpt:destinationStation", [""])[-1].split('.')[-1].strip()
    
    # 方向IDから日本語表示名を決める
    direction_jp = ""
    if direction_id and "InnerLoop" in direction_id:
        direction_jp = "内回り"
    elif direction_id and "OuterLoop" in direction_id:
        direction_jp = "外回り"
    else:
        direction_jp = "不明" # 念のため

    # 判定用のIDカードは「方向」と「行先」の組み合わせになる
    current_trip = (direction_id, dest_station_en)
    is_allowed = current_trip in line_config.get("regular_trips", {})
    
    # 戻り値: (非定期か?, 表示名)
    return not is_allowed, direction_jp

def process_irregularities(train_data, line_config):
    irregular_messages = []
    for train in train_data:
        # まず基本情報を取得
        train_type_id = train.get("odpt:trainType")
        train_number = train.get("odpt:trainNumber")
        line_id = line_config['id'] # 路線IDを先に取得
        
        # 必要な基本情報がなければスキップ
        if not all([train_type_id, train_number, line_id]): continue
        
        # 行き先リストを取得
        dest_station_id_list = train.get("odpt:destinationStation")

        is_irregular = False
        train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id) # デフォルト種別名
        dest_station_jp = "" # 行き先表示名を初期化
        notification_id = "" # 通知IDを初期化
        dest_station_en = "" # 英語の行き先名も初期化

        # ▼▼▼▼▼ 蛇窪ロマンルート ▼▼▼▼▼
        if line_id in HEBIKUBO_TARGET_LINES and dest_station_id_list is None:
            print(f"--- [HEBIKUBO?] Train {train_number} on {line_id} has None destination. Possible Hebikubo! ---", flush=True)
            is_irregular = True
            dest_station_jp = "蛇窪信号場" # 表示名を直接設定
            notification_id = f"{train_number}_Hebikubo" # 特別な通知ID
            # このルートでは dest_station_en は使わない

        # ▼▼▼ 通常ルート ▼▼▼
        else:
            if not dest_station_id_list: continue
        
        dest_station_en = dest_station_id_list[-1].split('.')[-1].strip()
        display_dest_en = dest_station_en
        notification_id = f"{train_number}_{dest_station_en}"
        
        is_irregular = False
        train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id) 
        line_id = line_config['id']


        # 【現場監督の判断】
        if line_config['id'] == 'odpt.Railway:JR-East.ChuoRapid':
            is_irregular, train_type_jp = check_chuo_line_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Chuo':
            is_irregular, train_type_jp = check_co_line_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Tokaido':
            is_irregular, train_type_jp, display_dest_en = check_tokaido_line_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Keiyo':
            is_irregular, train_type_jp = check_boso_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.SobuRapid':
            is_irregular, train_type_jp = check_boso_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Yokosuka':
            is_irregular, train_type_jp = check_suka_line_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Utsunomiya':
            is_irregular, train_type_jp = check_tohoku_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Takasaki':
            is_irregular, train_type_jp = check_tohoku_train(train, line_config.get("regular_trips", set()), TRAIN_TYPE_NAMES)
        elif line_config['id'] == 'odpt.Railway:JR-East.Yamanote':
            is_irregular, train_type_jp = _is_yamanote_line_train_irregular(train, line_config)

        
        else: # それ以外の路線
            current_trip = (train_type_id, dest_station_en)
            if current_trip not in line_config.get("regular_trips", {}):
                is_irregular = True
            train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id)
        
        if is_irregular and line_id == "odpt.Railway:JR-East.Keiyo":
            from_station_id = train.get("odpt:fromStation")
            to_station_id = train.get("odpt:toStation")
            direction = train.get("odpt:railDirection")
            
            # 条件: 蘇我駅に停車中 / Outbound / 列番末尾が A or Y
            if from_station_id and "Soga" in from_station_id and not to_station_id and \
               direction and "Outbound" in direction and \
               train_number: # train_numberがNoneでないことを確認
                 last_char = train_number[-1].upper() # 末尾の文字を大文字で取得
                 if last_char == 'A':
                     print(f"--- [KEIYO OVERRIDE] Train {train_number}: Overriding line name to Sotobo Line at Soga. ---", flush=True)
                     line_name_jp = "外房線" # 表示名を上書き
                 elif last_char == 'Y':
                     print(f"--- [KEIYO OVERRIDE] Train {train_number}: Overriding line name to Uchibo Line at Soga. ---", flush=True)
                     line_name_jp = "内房線" # 表示名を上書き

        if is_irregular and line_id == "odpt.Railway:JR-East.KeihinTohokuNegishi":
            direction = train.get("odpt:railDirection")
            current_location_id = train.get("odpt:toStation") or train.get("odpt:fromStation")

            # 条件: 快速 / 南行 / 浜松町以南 / 鶴見or東神奈川行き
            if train_type_id == 'odpt.TrainType:JR-East.Rapid' and \
               direction and "Southbound" in direction and \
               current_location_id and \
               dest_station_en in ['Tsurumi', 'Higashi-Kanagawa']:
                try:
                    hamamatsucho_index = KEIHIN_TOHOKU_STATIONS.index('浜松町')
                    current_station_name_en = current_location_id.split('.')[-1]
                    # 駅名辞書(STATION_DICT)を使って日本語名に変換
                    current_station_name_jp = STATION_DICT.get(current_station_name_en, "")

                    if current_station_name_jp and current_station_name_jp in KEIHIN_TOHOKU_STATIONS:
                         current_index = KEIHIN_TOHOKU_STATIONS.index(current_station_name_jp)
                         # 浜松町のインデックスより大きければ（南にいれば）見逃す
                         if current_index > hamamatsucho_index:
                             print(f"--- [K-TOHOKU SKIP] Train {train_number}: Skipping notification for Rapid to {dest_station_en} south of Hamamatsucho.", flush=True)
                             is_irregular = False # ★★★ 通知対象から除外 ★★★
                except (ValueError, IndexError, KeyError):
                     # 駅名が見つからない or インデックスエラーなどの場合は何もしない (is_irregular は True のまま)
                     print(f"--- [K-TOHOKU SKIP] Warning: Could not determine location for skip check on {train_number}. Station ID: {current_location_id}", flush=True)
                     pass
                
        is_special_name_from_specialist = train_type_jp not in TRAIN_TYPE_NAMES.values() and train_type_jp != train_type_id

        if is_irregular and notification_id and notification_id not in notified_trains:
            try:
                line_name_jp = line_config.get("name", "?")

                if not is_special_name_from_specialist:
             # ルール1: 特定路線の Local は「普通」
                    if train_type_id == 'odpt.TrainType:JR-East.Local' and \
                line_id in ['odpt.Railway:JR-East.Takasaki', 
                             'odpt.Railway:JR-East.Utsunomiya',
                             'odpt.Railway:JR-East.ShonanShinjuku', 
                             'odpt.Railway:JR-East.Yokosuka', 
                             'odpt.Railway:JR-East.Tokaido']:
                        train_type_jp = "普通"
             
             # ルール2: 特定路線の SpecialRapid は「ホリデー快速」
                    elif train_type_id == 'odpt.TrainType:JR-East.SpecialRapid' and \
                  line_id in ['odpt.Railway:JR-East.ChuoRapid', 
                              'odpt.Railway:JR-East.Ome']:
                        train_type_jp = "ホリデー快速"
             # 他にもルールがあれば elif で追加


                if "." in display_dest_en:
                    parts = display_dest_en.split('.')
                    dest_station_jp = "・".join([STATION_DICT.get(part, part) for part in parts])
                else:
                    dest_station_jp = STATION_DICT.get(dest_station_en, dest_station_en)
                location_text = ""
                from_station_id = train.get("odpt:fromStation")
                to_station_id = train.get("odpt:toStation")
                if to_station_id and from_station_id:
                    from_jp = STATION_DICT.get(from_station_id.split('.')[-1], from_station_id.split('.')[-1])
                    to_jp = STATION_DICT.get(to_station_id.split('.')[-1], to_station_id.split('.')[-1])
                    location_text = f"{from_jp}→{to_jp}を走行中"
                elif from_station_id:
                    from_jp = STATION_DICT.get(from_station_id.split('.')[-1], from_station_id.split('.')[-1])
                    location_text = f"{from_jp}に停車中"
                delay_minutes = round(train.get("odpt:delay", 0) / 60)
                delay_text = f"遅延:{delay_minutes}分" if delay_minutes > 0 else "定刻"
                message_line1 = f"[{line_name_jp}] {train_type_jp} {dest_station_jp}行き"
                # location_textが存在し、かつ遅延がある場合のみ遅延情報を追記
                location_text_with_delay = f"{location_text} ({delay_text})" if location_text and delay_text else location_text
                message_line2 = location_text_with_delay
                message_line3 = f"列番:{train_number}" # 列番のみ                
                final_message = f"{message_line1}\n{message_line2}\n{message_line3}" if message_line2 else f"{message_line1}\n{message_line3}"
                irregular_messages.append(final_message)
                notified_trains.add(notification_id)
            except Exception as e:
                print(f"--- [NOTIFICATION ERROR] Failed to create message for Train {train_number}. Error: {e}", flush=True)

    return irregular_messages

def check_jr_east_irregularities():
    all_irregular_trains = []
    for line_config in JR_LINES_TO_MONITOR:
        train_data = fetch_train_data(line_config)
        if train_data is not None:
            irregular_list = process_irregularities(train_data, line_config)
            all_irregular_trains.extend(irregular_list)
    return all_irregular_trains