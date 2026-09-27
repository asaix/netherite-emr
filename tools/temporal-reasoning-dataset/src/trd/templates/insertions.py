"""Contextual insertion templates for the insertions experiment.

Two types of insertions:
- Similar: Time-related distractors that are topically related to the task
- Dissimilar: Unrelated distractors that have no connection to temporal reasoning

All insertions are provided in 10 languages.
"""

import random
from typing import Dict, List

# Task type mappings for internal keys
_TASK_KEYS = ["addition_date", "subtraction_date", "addition_time", "subtraction_time",
              "duration_date", "duration_time", "recurrence_date", "interval_date", "day_of_week"]

# Similar insertions by language and task
SIMILAR_INSERTIONS: Dict[str, Dict[str, List[str]]] = {
    "en_US": {
        "addition_date": ["I always get confused with months that have 31 days.", "August is my favorite month of the year.", "I always forget how many days are in each month.", "It's interesting how we measure time in different cultures.", "The summer of 2025 has been quite interesting."],
        "subtraction_date": ["I always get confused with months that have 31 days.", "August is my favorite month of the year.", "I always forget how many days are in each month.", "It's interesting how we measure time in different cultures.", "The summer of 2025 has been quite interesting."],
        "addition_time": ["I always lose track of time in the morning.", "Time zones can be really confusing sometimes.", "My watch always runs a bit slow.", "The sunset is beautiful at this hour.", "I always lose track of time in the evening."],
        "subtraction_time": ["I always lose track of time in the morning.", "Time zones can be really confusing sometimes.", "My watch always runs a bit slow.", "The sunset is beautiful at this hour.", "I always lose track of time in the evening."],
        "duration_date": ["Time really flies when you're having fun.", "Spring dates are my favorite to keep track of.", "The calendar on my wall needs updating.", "I wonder if counting backwards with dates is harder than forwards.", "Time seems to move differently in spring compared to winter."],
        "duration_time": ["I never know if my watch is running fast.", "I should get my clock battery replaced soon.", "Time really flies during lunch break.", "I never understood why we don't use decimal time.", "The clock in my kitchen always shows different times."],
        "recurrence_date": ["Seven is actually my lucky number.", "February is such a unique month with its varying days.", "My scheduling app keeps crashing when I try to set this up.", "Dates in February always confuse me a bit.", "The last time I had a weekly commitment was in January."],
        "interval_date": ["Planning ahead helps me stay organized.", "Monday mornings are tough no matter what date it is.", "My calendar is filling up quickly this month.", "I always mix up dates in the middle of the month.", "Time seems to fly by in August."],
        "day_of_week": ["September always reminds me of fall leaves.", "The 22nd seems to come around faster each month.", "I prefer knowing weekdays for planning purposes.", "Calendar dates can be so confusing sometimes.", "I wonder if it will be a sunny day."],
    },
    "es_ES": {
        "addition_date": ["Siempre me confundo con los meses que tienen 31 días.", "Agosto es mi mes favorito del año.", "Siempre olvido cuántos días tiene cada mes.", "Es interesante cómo medimos el tiempo en diferentes culturas.", "El verano de 2025 ha sido bastante interesante."],
        "subtraction_date": ["Siempre me confundo con los meses que tienen 31 días.", "Agosto es mi mes favorito del año.", "Siempre olvido cuántos días tiene cada mes.", "Es interesante cómo medimos el tiempo en diferentes culturas.", "El verano de 2025 ha sido bastante interesante."],
        "addition_time": ["Siempre pierdo la noción del tiempo por la mañana.", "Las zonas horarias pueden ser muy confusas a veces.", "Mi reloj siempre va un poco lento.", "La puesta del sol es hermosa a esta hora.", "Siempre pierdo la noción del tiempo por la noche."],
        "subtraction_time": ["Siempre pierdo la noción del tiempo por la mañana.", "Las zonas horarias pueden ser muy confusas a veces.", "Mi reloj siempre va un poco lento.", "La puesta del sol es hermosa a esta hora.", "Siempre pierdo la noción del tiempo por la noche."],
        "duration_date": ["El tiempo realmente vuela cuando te diviertes.", "Las fechas de primavera son mis favoritas.", "El calendario en mi pared necesita actualizarse.", "Me pregunto si contar hacia atrás es más difícil.", "El tiempo parece moverse diferente en primavera."],
        "duration_time": ["Nunca sé si mi reloj va adelantado.", "Debería cambiar la batería de mi reloj pronto.", "El tiempo vuela durante la hora del almuerzo.", "Nunca entendí por qué no usamos el tiempo decimal.", "El reloj de mi cocina siempre muestra horas diferentes."],
        "recurrence_date": ["El siete es mi número de la suerte.", "Febrero es un mes único con sus días variables.", "Mi aplicación de programación sigue fallando.", "Las fechas en febrero siempre me confunden.", "La última vez que tuve un compromiso semanal fue en enero."],
        "interval_date": ["Planificar con anticipación me ayuda a organizarme.", "Las mañanas de lunes son difíciles sin importar la fecha.", "Mi calendario se está llenando rápidamente este mes.", "Siempre confundo las fechas a mitad de mes.", "El tiempo parece volar en agosto."],
        "day_of_week": ["Septiembre siempre me recuerda las hojas de otoño.", "El 22 parece llegar más rápido cada mes.", "Prefiero conocer los días de la semana para planificar.", "Las fechas del calendario pueden ser confusas.", "Me pregunto si será un día soleado."],
    },
    "de_DE": {
        "addition_date": ["Ich werde immer verwirrt bei Monaten mit 31 Tagen.", "August ist mein Lieblingsmonat.", "Ich vergesse immer, wie viele Tage jeder Monat hat.", "Es ist interessant, wie wir Zeit in verschiedenen Kulturen messen.", "Der Sommer 2025 war ziemlich interessant."],
        "subtraction_date": ["Ich werde immer verwirrt bei Monaten mit 31 Tagen.", "August ist mein Lieblingsmonat.", "Ich vergesse immer, wie viele Tage jeder Monat hat.", "Es ist interessant, wie wir Zeit in verschiedenen Kulturen messen.", "Der Sommer 2025 war ziemlich interessant."],
        "addition_time": ["Morgens verliere ich immer mein Zeitgefühl.", "Zeitzonen können verwirrend sein.", "Meine Uhr geht immer etwas nach.", "Der Sonnenuntergang ist wunderschön.", "Abends verliere ich immer mein Zeitgefühl."],
        "subtraction_time": ["Morgens verliere ich immer mein Zeitgefühl.", "Zeitzonen können verwirrend sein.", "Meine Uhr geht immer etwas nach.", "Der Sonnenuntergang ist wunderschön.", "Abends verliere ich immer mein Zeitgefühl."],
        "duration_date": ["Die Zeit vergeht schnell, wenn man Spaß hat.", "Frühlingsdaten sind meine Liebsten.", "Der Kalender muss aktualisiert werden.", "Ich frage mich, ob Rückwärtszählen schwieriger ist.", "Die Zeit bewegt sich im Frühling anders."],
        "duration_time": ["Ich weiß nie, ob meine Uhr vorgeht.", "Ich sollte die Batterie meiner Uhr wechseln.", "Die Zeit vergeht schnell in der Mittagspause.", "Ich verstehe nicht, warum wir keine Dezimalzeit nutzen.", "Die Uhr in meiner Küche zeigt verschiedene Zeiten."],
        "recurrence_date": ["Sieben ist meine Glückszahl.", "Februar ist ein einzigartiger Monat.", "Meine Terminplanungs-App stürzt ab.", "Daten im Februar verwirren mich.", "Meine letzte wöchentliche Verpflichtung war im Januar."],
        "interval_date": ["Vorausplanen hilft mir organisiert zu bleiben.", "Montagmorgen sind schwer, egal welches Datum.", "Mein Kalender füllt sich schnell.", "Ich verwechsle Daten in der Monatsmitte.", "Die Zeit verfliegt im August."],
        "day_of_week": ["September erinnert mich an Herbstlaub.", "Der 22. kommt jeden Monat schneller.", "Ich bevorzuge Wochentage für die Planung.", "Kalenderdaten können verwirrend sein.", "Ich frage mich, ob es sonnig wird."],
    },
    "fr_FR": {
        "addition_date": ["Je me mélange avec les mois de 31 jours.", "Août est mon mois préféré.", "J'oublie combien de jours il y a dans chaque mois.", "C'est intéressant comment on mesure le temps.", "L'été 2025 a été intéressant."],
        "subtraction_date": ["Je me mélange avec les mois de 31 jours.", "Août est mon mois préféré.", "J'oublie combien de jours il y a dans chaque mois.", "C'est intéressant comment on mesure le temps.", "L'été 2025 a été intéressant."],
        "addition_time": ["Je perds la notion du temps le matin.", "Les fuseaux horaires sont déroutants.", "Ma montre retarde toujours.", "Le coucher de soleil est magnifique.", "Je perds la notion du temps le soir."],
        "subtraction_time": ["Je perds la notion du temps le matin.", "Les fuseaux horaires sont déroutants.", "Ma montre retarde toujours.", "Le coucher de soleil est magnifique.", "Je perds la notion du temps le soir."],
        "duration_date": ["Le temps passe vite quand on s'amuse.", "Les dates du printemps sont mes préférées.", "Le calendrier a besoin d'être mis à jour.", "Compter à rebours est-il plus difficile?", "Le temps semble différent au printemps."],
        "duration_time": ["Je ne sais jamais si ma montre avance.", "Je devrais remplacer la pile de mon horloge.", "Le temps passe vite pendant le déjeuner.", "Pourquoi n'utilisons-nous pas le temps décimal?", "L'horloge de ma cuisine affiche différentes heures."],
        "recurrence_date": ["Sept est mon chiffre porte-bonheur.", "Février est un mois unique.", "Mon application de planification plante.", "Les dates en février me confondent.", "Mon dernier engagement hebdomadaire était en janvier."],
        "interval_date": ["Planifier à l'avance m'aide à rester organisé.", "Les lundis matin sont difficiles.", "Mon calendrier se remplit rapidement.", "Je mélange les dates au milieu du mois.", "Le temps file en août."],
        "day_of_week": ["Septembre me rappelle les feuilles d'automne.", "Le 22 arrive plus vite chaque mois.", "Je préfère connaître les jours de la semaine.", "Les dates du calendrier sont déroutantes.", "Fera-t-il beau?"],
    },
    "it_IT": {
        "addition_date": ["Mi confondo sempre con i mesi di 31 giorni.", "Agosto è il mio mese preferito.", "Dimentico quanti giorni ci sono in ogni mese.", "È interessante come misuriamo il tempo.", "L'estate del 2025 è stata interessante."],
        "subtraction_date": ["Mi confondo sempre con i mesi di 31 giorni.", "Agosto è il mio mese preferito.", "Dimentico quanti giorni ci sono in ogni mese.", "È interessante come misuriamo il tempo.", "L'estate del 2025 è stata interessante."],
        "addition_time": ["Perdo la cognizione del tempo la mattina.", "I fusi orari possono essere confusi.", "Il mio orologio va indietro.", "Il tramonto è bellissimo.", "Perdo la cognizione del tempo la sera."],
        "subtraction_time": ["Perdo la cognizione del tempo la mattina.", "I fusi orari possono essere confusi.", "Il mio orologio va indietro.", "Il tramonto è bellissimo.", "Perdo la cognizione del tempo la sera."],
        "duration_date": ["Il tempo vola quando ci si diverte.", "Le date primaverili sono le mie preferite.", "Il calendario deve essere aggiornato.", "Contare all'indietro è più difficile?", "Il tempo sembra diverso in primavera."],
        "duration_time": ["Non so mai se il mio orologio va avanti.", "Dovrei sostituire la batteria dell'orologio.", "Il tempo vola durante la pausa pranzo.", "Perché non usiamo il tempo decimale?", "L'orologio in cucina mostra orari diversi."],
        "recurrence_date": ["Il sette è il mio numero fortunato.", "Febbraio è un mese unico.", "La mia app di pianificazione continua a crashare.", "Le date di febbraio mi confondono.", "L'ultimo impegno settimanale era a gennaio."],
        "interval_date": ["Pianificare in anticipo mi aiuta a restare organizzato.", "I lunedì mattina sono difficili.", "Il mio calendario si riempie velocemente.", "Confondo le date a metà mese.", "Il tempo vola in agosto."],
        "day_of_week": ["Settembre mi ricorda le foglie autunnali.", "Il 22 arriva più velocemente ogni mese.", "Preferisco sapere i giorni della settimana.", "Le date del calendario sono confuse.", "Sarà una giornata soleggiata?"],
    },
    "pt_BR": {
        "addition_date": ["Eu fico confuso com os meses de 31 dias.", "Agosto é meu mês favorito.", "Esqueço quantos dias cada mês tem.", "É interessante como medimos o tempo.", "O verão de 2025 foi interessante."],
        "subtraction_date": ["Eu fico confuso com os meses de 31 dias.", "Agosto é meu mês favorito.", "Esqueço quantos dias cada mês tem.", "É interessante como medimos o tempo.", "O verão de 2025 foi interessante."],
        "addition_time": ["Perdo a noção do tempo de manhã.", "Fusos horários podem ser confusos.", "Meu relógio sempre atrasa.", "O pôr do sol está lindo.", "Perdo a noção do tempo à noite."],
        "subtraction_time": ["Perdo a noção do tempo de manhã.", "Fusos horários podem ser confusos.", "Meu relógio sempre atrasa.", "O pôr do sol está lindo.", "Perdo a noção do tempo à noite."],
        "duration_date": ["O tempo voa quando você se diverte.", "As datas da primavera são minhas favoritas.", "O calendário precisa ser atualizado.", "Contar para trás é mais difícil?", "O tempo parece diferente na primavera."],
        "duration_time": ["Nunca sei se meu relógio está adiantado.", "Deveria trocar a bateria do relógio.", "O tempo voa durante o almoço.", "Por que não usamos o tempo decimal?", "O relógio da cozinha mostra horários diferentes."],
        "recurrence_date": ["Sete é meu número da sorte.", "Fevereiro é um mês único.", "Meu aplicativo de agenda trava.", "As datas de fevereiro me confundem.", "Meu último compromisso semanal foi em janeiro."],
        "interval_date": ["Planejar com antecedência me ajuda a ficar organizado.", "As segundas de manhã são difíceis.", "Meu calendário está se enchendo rápido.", "Confundo datas no meio do mês.", "O tempo voa em agosto."],
        "day_of_week": ["Setembro me lembra das folhas de outono.", "O dia 22 chega mais rápido a cada mês.", "Prefiro saber os dias da semana para planejar.", "Datas do calendário são confusas.", "Será um dia ensolarado?"],
    },
    "nl_NL": {
        "addition_date": ["Ik raak in de war met maanden van 31 dagen.", "Augustus is mijn favoriete maand.", "Ik vergeet hoeveel dagen elke maand heeft.", "Het is interessant hoe we tijd meten.", "De zomer van 2025 was interessant."],
        "subtraction_date": ["Ik raak in de war met maanden van 31 dagen.", "Augustus is mijn favoriete maand.", "Ik vergeet hoeveel dagen elke maand heeft.", "Het is interessant hoe we tijd meten.", "De zomer van 2025 was interessant."],
        "addition_time": ["Ik verlies 's ochtends het besef van tijd.", "Tijdzones kunnen verwarrend zijn.", "Mijn horloge loopt altijd achter.", "De zonsondergang is prachtig.", "Ik verlies 's avonds het besef van tijd."],
        "subtraction_time": ["Ik verlies 's ochtends het besef van tijd.", "Tijdzones kunnen verwarrend zijn.", "Mijn horloge loopt altijd achter.", "De zonsondergang is prachtig.", "Ik verlies 's avonds het besef van tijd."],
        "duration_date": ["De tijd vliegt als je plezier hebt.", "Lentedata zijn mijn favoriete.", "De kalender moet bijgewerkt worden.", "Is achteruit tellen moeilijker?", "De tijd lijkt anders in de lente."],
        "duration_time": ["Ik weet nooit of mijn horloge voor loopt.", "Ik zou de batterij van mijn klok moeten vervangen.", "De tijd vliegt tijdens de lunch.", "Waarom gebruiken we geen decimale tijd?", "De klok in mijn keuken laat verschillende tijden zien."],
        "recurrence_date": ["Zeven is mijn geluksnummer.", "Februari is een unieke maand.", "Mijn agenda-app blijft crashen.", "Datums in februari verwarren me.", "Mijn laatste wekelijkse verplichting was in januari."],
        "interval_date": ["Vooruit plannen helpt me georganiseerd te blijven.", "Maandagochtenden zijn moeilijk.", "Mijn kalender vult zich snel.", "Ik verwar datums in het midden van de maand.", "De tijd vliegt in augustus."],
        "day_of_week": ["September herinnert me aan herfstbladeren.", "De 22e komt elke maand sneller.", "Ik weet graag welke dag van de week het is.", "Kalenderdatums zijn verwarrend.", "Wordt het een zonnige dag?"],
    },
    "ja_JP": {
        "addition_date": ["31日ある月といつも混乱します。", "8月は一番好きな月です。", "各月が何日あるのかいつも忘れます。", "異なる文化での時間の測り方は興味深いです。", "2025年の夏は興味深かったです。"],
        "subtraction_date": ["31日ある月といつも混乱します。", "8月は一番好きな月です。", "各月が何日あるのかいつも忘れます。", "異なる文化での時間の測り方は興味深いです。", "2025年の夏は興味深かったです。"],
        "addition_time": ["朝は時間を見失います。", "タイムゾーンは混乱します。", "私の時計は少し遅れています。", "この時間の夕日は美しいです。", "夕方は時間を見失います。"],
        "subtraction_time": ["朝は時間を見失います。", "タイムゾーンは混乱します。", "私の時計は少し遅れています。", "この時間の夕日は美しいです。", "夕方は時間を見失います。"],
        "duration_date": ["楽しい時は時間が早く過ぎます。", "春の日付が一番好きです。", "壁のカレンダーを更新する必要があります。", "逆に数えるのは難しいですか？", "春は時間の流れ方が違います。"],
        "duration_time": ["時計が進んでいるかわかりません。", "時計の電池を交換すべきです。", "昼休みは時間が早く過ぎます。", "なぜ10進法の時間を使わないのですか？", "キッチンの時計は違う時間を示します。"],
        "recurrence_date": ["7は私のラッキーナンバーです。", "2月はユニークな月です。", "スケジュールアプリがクラッシュします。", "2月の日付は混乱します。", "最後の週次の約束は1月でした。"],
        "interval_date": ["事前に計画すると整理できます。", "月曜日の朝は大変です。", "今月はカレンダーがすぐに埋まります。", "月の半ばの日付を間違えます。", "8月は時間が飛ぶように過ぎます。"],
        "day_of_week": ["9月は秋の葉を思い出させます。", "22日は毎月早く来ます。", "計画のために曜日を知りたいです。", "カレンダーの日付は混乱します。", "晴れの日になるかな。"],
    },
    "ar_SA": {
        "addition_date": ["أشعر بالارتباك مع الأشهر التي تحتوي على 31 يوماً.", "أغسطس هو شهري المفضل.", "أنسى عدد الأيام في كل شهر.", "من المثير كيف نقيس الوقت في الثقافات المختلفة.", "كان صيف 2025 مثيراً للاهتمام."],
        "subtraction_date": ["أشعر بالارتباك مع الأشهر التي تحتوي على 31 يوماً.", "أغسطس هو شهري المفضل.", "أنسى عدد الأيام في كل شهر.", "من المثير كيف نقيس الوقت في الثقافات المختلفة.", "كان صيف 2025 مثيراً للاهتمام."],
        "addition_time": ["أفقد إحساسي بالوقت في الصباح.", "المناطق الزمنية محيرة أحياناً.", "ساعتي تتأخر دائماً.", "غروب الشمس جميل.", "أفقد إحساسي بالوقت في المساء."],
        "subtraction_time": ["أفقد إحساسي بالوقت في الصباح.", "المناطق الزمنية محيرة أحياناً.", "ساعتي تتأخر دائماً.", "غروب الشمس جميل.", "أفقد إحساسي بالوقت في المساء."],
        "duration_date": ["الوقت يمر بسرعة عندما تستمتع.", "تواريخ الربيع هي المفضلة لدي.", "التقويم يحتاج إلى تحديث.", "هل العد للخلف أصعب؟", "الوقت يتحرك بشكل مختلف في الربيع."],
        "duration_time": ["لا أعرف إن كانت ساعتي متقدمة.", "يجب أن أستبدل بطارية ساعتي.", "الوقت يمر بسرعة خلال الغداء.", "لماذا لا نستخدم الوقت العشري؟", "ساعة مطبخي تظهر أوقاتاً مختلفة."],
        "recurrence_date": ["السبعة هو رقم حظي.", "فبراير شهر فريد.", "تطبيق الجدولة يتعطل.", "تواريخ فبراير تربكني.", "آخر التزام أسبوعي كان في يناير."],
        "interval_date": ["التخطيط المسبق يساعدني على التنظيم.", "صباحات الاثنين صعبة.", "تقويمي يمتلئ بسرعة.", "أخلط بين التواريخ في منتصف الشهر.", "الوقت يمر بسرعة في أغسطس."],
        "day_of_week": ["سبتمبر يذكرني بأوراق الخريف.", "يبدو أن الـ22 يأتي أسرع كل شهر.", "أفضل معرفة أيام الأسبوع للتخطيط.", "تواريخ التقويم محيرة.", "هل سيكون يوماً مشمساً؟"],
    },
    "hi_IN": {
        "addition_date": ["मुझे 31 दिनों वाले महीनों में भ्रम होता है।", "अगस्त मेरा पसंदीदा महीना है।", "मैं भूल जाता हूं कि हर महीने में कितने दिन होते हैं।", "यह दिलचस्प है कि हम समय कैसे मापते हैं।", "2025 की गर्मी दिलचस्प रही।"],
        "subtraction_date": ["मुझे 31 दिनों वाले महीनों में भ्रम होता है।", "अगस्त मेरा पसंदीदा महीना है।", "मैं भूल जाता हूं कि हर महीने में कितने दिन होते हैं।", "यह दिलचस्प है कि हम समय कैसे मापते हैं।", "2025 की गर्मी दिलचस्प रही।"],
        "addition_time": ["सुबह मुझे समय का ध्यान नहीं रहता।", "समय क्षेत्र भ्रमित करने वाले हो सकते हैं।", "मेरी घड़ी धीमी चलती है।", "इस समय सूर्यास्त सुंदर है।", "शाम को मुझे समय का ध्यान नहीं रहता।"],
        "subtraction_time": ["सुबह मुझे समय का ध्यान नहीं रहता।", "समय क्षेत्र भ्रमित करने वाले हो सकते हैं।", "मेरी घड़ी धीमी चलती है।", "इस समय सूर्यास्त सुंदर है।", "शाम को मुझे समय का ध्यान नहीं रहता।"],
        "duration_date": ["मज़े करते समय वक्त उड़ जाता है।", "वसंत की तारीखें मेरी पसंदीदा हैं।", "कैलेंडर को अपडेट करना है।", "क्या उल्टा गिनना कठिन है?", "वसंत में समय अलग चलता है।"],
        "duration_time": ["मुझे नहीं पता कि मेरी घड़ी तेज़ है या नहीं।", "मुझे घड़ी की बैटरी बदलनी चाहिए।", "लंच में समय उड़ जाता है।", "हम दशमलव समय क्यों नहीं उपयोग करते?", "किचन की घड़ी अलग समय दिखाती है।"],
        "recurrence_date": ["सात मेरा भाग्यशाली नंबर है।", "फरवरी एक अनोखा महीना है।", "मेरा शेड्यूलिंग ऐप क्रैश होता है।", "फरवरी की तारीखें भ्रमित करती हैं।", "आखिरी साप्ताहिक प्रतिबद्धता जनवरी में थी।"],
        "interval_date": ["पहले से योजना बनाने से संगठित रहता हूं।", "सोमवार की सुबह कठिन होती है।", "इस महीने कैलेंडर भर रहा है।", "महीने के बीच की तारीखें भूल जाता हूं।", "अगस्त में समय उड़ जाता है।"],
        "day_of_week": ["सितंबर पतझड़ की याद दिलाता है।", "22 तारीख हर महीने जल्दी आती है।", "योजना के लिए दिन जानना पसंद है।", "कैलेंडर की तारीखें भ्रमित करती हैं।", "क्या धूप वाला दिन होगा?"],
    },
}

# Dissimilar insertions by language and task - unrelated to temporal reasoning
DISSIMILAR_INSERTIONS: Dict[str, Dict[str, List[str]]] = {
    "en_US": {
        "addition_date": ["The garden needs new flowers.", "My brother bought a motorcycle.", "The recipe calls for sugar.", "Classical music helps me concentrate.", "The museum opens at nine."],
        "subtraction_date": ["I need new running shoes.", "The library closes at 8 PM.", "My favorite color is purple.", "Coffee tastes better with milk.", "Birds fly south for winter."],
        "addition_time": ["The mountain was covered in snow.", "My grandmother's recipe uses vanilla.", "Electric cars are popular.", "The library expanded its section.", "Bamboo grows quickly."],
        "subtraction_time": ["Maple trees turn colors in autumn.", "Space telescopes capture images.", "Fresh bread smells wonderful.", "Tennis needs coordination.", "Dolphins communicate with clicks."],
        "duration_date": ["The Sahara has rock formations.", "Violins have four strings.", "Bamboo can grow very fast.", "Blue whales use low sounds.", "Fresh basil adds flavor."],
        "duration_time": ["Sunflowers grew tall this year.", "My cousin plays the violin.", "Blue whales weigh a lot.", "The recipe uses basil.", "Japan has many islands."],
        "recurrence_date": ["The sky looks blue today.", "My neighbor bought a bicycle.", "Fresh bread smells wonderful.", "Penguins are great swimmers.", "The library has nice chairs."],
        "interval_date": ["The oak tree provides shade.", "Sea turtles hold their breath.", "My grandmother's lasagna uses cheese.", "The Great Wall took years to build.", "Electric cars are popular."],
        "day_of_week": ["Ocean waves crash on rocks.", "My grandmother uses fresh basil.", "Solar panels need sunlight.", "That documentary was fascinating.", "The wooden chair needs paint."],
    },
    "es_ES": {
        "addition_date": ["El jardín necesita flores nuevas.", "Mi hermano compró una motocicleta.", "La receta requiere azúcar.", "La música clásica me ayuda a concentrarme.", "El museo abre a las nueve."],
        "subtraction_date": ["Necesito zapatos nuevos para correr.", "La biblioteca cierra a las 8 PM.", "Mi color favorito es el morado.", "El café sabe mejor con leche.", "Los pájaros vuelan al sur en invierno."],
        "addition_time": ["La montaña estaba cubierta de nieve.", "La receta de mi abuela usa vainilla.", "Los coches eléctricos son populares.", "La biblioteca amplió su sección.", "El bambú crece rápidamente."],
        "subtraction_time": ["Los arces cambian de color en otoño.", "Los telescopios espaciales capturan imágenes.", "El pan fresco huele maravilloso.", "El tenis requiere coordinación.", "Los delfines se comunican con clics."],
        "duration_date": ["El Sahara tiene formaciones rocosas.", "Los violines tienen cuatro cuerdas.", "El bambú puede crecer muy rápido.", "Las ballenas azules usan sonidos bajos.", "La albahaca fresca añade sabor."],
        "duration_time": ["Los girasoles crecieron altos este año.", "Mi primo toca el violín.", "Las ballenas azules pesan mucho.", "La receta usa albahaca.", "Japón tiene muchas islas."],
        "recurrence_date": ["El cielo se ve azul hoy.", "Mi vecino compró una bicicleta.", "El pan fresco huele maravilloso.", "Los pingüinos son grandes nadadores.", "La biblioteca tiene sillas cómodas."],
        "interval_date": ["El roble proporciona sombra.", "Las tortugas marinas aguantan la respiración.", "La lasaña de mi abuela usa queso.", "La Gran Muralla tardó años en construirse.", "Los coches eléctricos son populares."],
        "day_of_week": ["Las olas del océano chocan contra las rocas.", "Mi abuela usa albahaca fresca.", "Los paneles solares necesitan luz solar.", "Ese documental fue fascinante.", "La silla de madera necesita pintura."],
    },
    "de_DE": {
        "addition_date": ["Der Garten braucht neue Blumen.", "Mein Bruder kaufte ein Motorrad.", "Das Rezept benötigt Zucker.", "Klassische Musik hilft mir.", "Das Museum öffnet um neun."],
        "subtraction_date": ["Ich brauche neue Laufschuhe.", "Die Bibliothek schließt um 20 Uhr.", "Meine Lieblingsfarbe ist lila.", "Kaffee schmeckt besser mit Milch.", "Vögel fliegen im Winter nach Süden."],
        "addition_time": ["Der Berg war schneebedeckt.", "Omas Rezept verwendet Vanille.", "Elektroautos sind beliebt.", "Die Bibliothek erweiterte ihre Abteilung.", "Bambus wächst schnell."],
        "subtraction_time": ["Ahornbäume färben sich im Herbst.", "Weltraumteleskope erfassen Bilder.", "Frisches Brot riecht wunderbar.", "Tennis erfordert Koordination.", "Delfine kommunizieren mit Klicks."],
        "duration_date": ["Die Sahara hat Felsformationen.", "Geigen haben vier Saiten.", "Bambus kann sehr schnell wachsen.", "Blauwale nutzen tiefe Töne.", "Frisches Basilikum gibt Geschmack."],
        "duration_time": ["Sonnenblumen wuchsen dieses Jahr hoch.", "Mein Cousin spielt Geige.", "Blauwale wiegen viel.", "Das Rezept verwendet Basilikum.", "Japan hat viele Inseln."],
        "recurrence_date": ["Der Himmel sieht heute blau aus.", "Mein Nachbar kaufte ein Fahrrad.", "Frisches Brot riecht wunderbar.", "Pinguine sind tolle Schwimmer.", "Die Bibliothek hat bequeme Stühle."],
        "interval_date": ["Die Eiche spendet Schatten.", "Meeresschildkröten halten die Luft an.", "Omas Lasagne verwendet Käse.", "Die Große Mauer brauchte Jahre.", "Elektroautos sind beliebt."],
        "day_of_week": ["Ozeanwellen brechen an Felsen.", "Meine Oma verwendet frisches Basilikum.", "Solarpanele brauchen Sonnenlicht.", "Diese Dokumentation war faszinierend.", "Der Holzstuhl braucht Farbe."],
    },
    "fr_FR": {
        "addition_date": ["Le jardin a besoin de fleurs.", "Mon frère a acheté une moto.", "La recette demande du sucre.", "La musique classique m'aide.", "Le musée ouvre à neuf heures."],
        "subtraction_date": ["J'ai besoin de chaussures de course.", "La bibliothèque ferme à 20h.", "Ma couleur préférée est le violet.", "Le café est meilleur avec du lait.", "Les oiseaux volent vers le sud."],
        "addition_time": ["La montagne était enneigée.", "La recette de grand-mère utilise de la vanille.", "Les voitures électriques sont populaires.", "La bibliothèque a agrandi sa section.", "Le bambou pousse vite."],
        "subtraction_time": ["Les érables changent de couleur en automne.", "Les télescopes spatiaux capturent des images.", "Le pain frais sent bon.", "Le tennis demande de la coordination.", "Les dauphins communiquent par clics."],
        "duration_date": ["Le Sahara a des formations rocheuses.", "Les violons ont quatre cordes.", "Le bambou peut pousser très vite.", "Les baleines bleues utilisent des sons graves.", "Le basilic frais ajoute de la saveur."],
        "duration_time": ["Les tournesols ont poussé haut cette année.", "Mon cousin joue du violon.", "Les baleines bleues pèsent beaucoup.", "La recette utilise du basilic.", "Le Japon a beaucoup d'îles."],
        "recurrence_date": ["Le ciel est bleu aujourd'hui.", "Mon voisin a acheté un vélo.", "Le pain frais sent bon.", "Les pingouins sont d'excellents nageurs.", "La bibliothèque a des chaises confortables."],
        "interval_date": ["Le chêne fournit de l'ombre.", "Les tortues marines retiennent leur souffle.", "La lasagne de grand-mère utilise du fromage.", "La Grande Muraille a pris des années.", "Les voitures électriques sont populaires."],
        "day_of_week": ["Les vagues de l'océan frappent les rochers.", "Ma grand-mère utilise du basilic frais.", "Les panneaux solaires ont besoin de soleil.", "Ce documentaire était fascinant.", "La chaise en bois a besoin de peinture."],
    },
    "it_IT": {
        "addition_date": ["Il giardino ha bisogno di fiori.", "Mio fratello ha comprato una moto.", "La ricetta richiede zucchero.", "La musica classica mi aiuta.", "Il museo apre alle nove."],
        "subtraction_date": ["Ho bisogno di scarpe da corsa.", "La biblioteca chiude alle 20.", "Il mio colore preferito è il viola.", "Il caffè è meglio con il latte.", "Gli uccelli volano a sud in inverno."],
        "addition_time": ["La montagna era coperta di neve.", "La ricetta della nonna usa la vaniglia.", "Le auto elettriche sono popolari.", "La biblioteca ha ampliato la sezione.", "Il bambù cresce velocemente."],
        "subtraction_time": ["Gli aceri cambiano colore in autunno.", "I telescopi spaziali catturano immagini.", "Il pane fresco profuma bene.", "Il tennis richiede coordinazione.", "I delfini comunicano con clic."],
        "duration_date": ["Il Sahara ha formazioni rocciose.", "I violini hanno quattro corde.", "Il bambù può crescere molto velocemente.", "Le balene blu usano suoni bassi.", "Il basilico fresco aggiunge sapore."],
        "duration_time": ["I girasoli sono cresciuti alti quest'anno.", "Mio cugino suona il violino.", "Le balene blu pesano molto.", "La ricetta usa il basilico.", "Il Giappone ha molte isole."],
        "recurrence_date": ["Il cielo è azzurro oggi.", "Il mio vicino ha comprato una bici.", "Il pane fresco profuma bene.", "I pinguini sono ottimi nuotatori.", "La biblioteca ha sedie comode."],
        "interval_date": ["La quercia fornisce ombra.", "Le tartarughe marine trattengono il respiro.", "La lasagna della nonna usa il formaggio.", "La Grande Muraglia ha richiesto anni.", "Le auto elettriche sono popolari."],
        "day_of_week": ["Le onde dell'oceano si infrangono sulle rocce.", "Mia nonna usa basilico fresco.", "I pannelli solari hanno bisogno di luce solare.", "Quel documentario era affascinante.", "La sedia di legno ha bisogno di vernice."],
    },
    "pt_BR": {
        "addition_date": ["O jardim precisa de flores novas.", "Meu irmão comprou uma moto.", "A receita pede açúcar.", "Música clássica me ajuda a concentrar.", "O museu abre às nove."],
        "subtraction_date": ["Preciso de tênis novos.", "A biblioteca fecha às 20h.", "Minha cor favorita é roxo.", "Café fica melhor com leite.", "Pássaros voam para o sul no inverno."],
        "addition_time": ["A montanha estava coberta de neve.", "A receita da vovó usa baunilha.", "Carros elétricos são populares.", "A biblioteca expandiu sua seção.", "Bambu cresce rapidamente."],
        "subtraction_time": ["Bordos mudam de cor no outono.", "Telescópios espaciais capturam imagens.", "Pão fresco cheira maravilhosamente.", "Tênis requer coordenação.", "Golfinhos se comunicam com cliques."],
        "duration_date": ["O Saara tem formações rochosas.", "Violinos têm quatro cordas.", "Bambu pode crescer muito rápido.", "Baleias azuis usam sons graves.", "Manjericão fresco adiciona sabor."],
        "duration_time": ["Os girassóis cresceram altos este ano.", "Meu primo toca violino.", "Baleias azuis pesam muito.", "A receita usa manjericão.", "O Japão tem muitas ilhas."],
        "recurrence_date": ["O céu está azul hoje.", "Meu vizinho comprou uma bicicleta.", "Pão fresco cheira maravilhosamente.", "Pinguins são ótimos nadadores.", "A biblioteca tem cadeiras confortáveis."],
        "interval_date": ["O carvalho fornece sombra.", "Tartarugas marinhas prendem a respiração.", "A lasanha da vovó usa queijo.", "A Grande Muralha levou anos.", "Carros elétricos são populares."],
        "day_of_week": ["Ondas do oceano batem nas rochas.", "Minha avó usa manjericão fresco.", "Painéis solares precisam de luz solar.", "Aquele documentário foi fascinante.", "A cadeira de madeira precisa de tinta."],
    },
    "nl_NL": {
        "addition_date": ["De tuin heeft nieuwe bloemen nodig.", "Mijn broer kocht een motor.", "Het recept vraagt om suiker.", "Klassieke muziek helpt me.", "Het museum opent om negen uur."],
        "subtraction_date": ["Ik heb nieuwe hardloopschoenen nodig.", "De bibliotheek sluit om 20.00 uur.", "Mijn favoriete kleur is paars.", "Koffie smaakt beter met melk.", "Vogels vliegen naar het zuiden in de winter."],
        "addition_time": ["De berg was bedekt met sneeuw.", "Oma's recept gebruikt vanille.", "Elektrische auto's zijn populair.", "De bibliotheek breidde haar sectie uit.", "Bamboe groeit snel."],
        "subtraction_time": ["Esdoorns verkleuren in de herfst.", "Ruimtetelescopen maken beelden.", "Vers brood ruikt heerlijk.", "Tennis vereist coördinatie.", "Dolfijnen communiceren met klikken."],
        "duration_date": ["De Sahara heeft rotsformaties.", "Violen hebben vier snaren.", "Bamboe kan heel snel groeien.", "Blauwe vinvissen gebruiken lage geluiden.", "Verse basilicum geeft smaak."],
        "duration_time": ["Zonnebloemen groeiden dit jaar hoog.", "Mijn neef speelt viool.", "Blauwe vinvissen wegen veel.", "Het recept gebruikt basilicum.", "Japan heeft veel eilanden."],
        "recurrence_date": ["De lucht ziet er blauw uit vandaag.", "Mijn buurman kocht een fiets.", "Vers brood ruikt heerlijk.", "Pinguïns zijn geweldige zwemmers.", "De bibliotheek heeft comfortabele stoelen."],
        "interval_date": ["De eik geeft schaduw.", "Zeeschildpadden houden hun adem in.", "Oma's lasagne gebruikt kaas.", "De Chinese Muur duurde jaren.", "Elektrische auto's zijn populair."],
        "day_of_week": ["Oceaangolven slaan op rotsen.", "Mijn oma gebruikt verse basilicum.", "Zonnepanelen hebben zonlicht nodig.", "Die documentaire was fascinerend.", "De houten stoel heeft verf nodig."],
    },
    "ja_JP": {
        "addition_date": ["庭に新しい花が必要です。", "兄がバイクを買いました。", "レシピには砂糖が必要です。", "クラシック音楽は集中に役立ちます。", "美術館は9時に開きます。"],
        "subtraction_date": ["新しいランニングシューズが必要です。", "図書館は20時に閉まります。", "私の好きな色は紫です。", "コーヒーはミルクと美味しいです。", "鳥は冬に南へ飛びます。"],
        "addition_time": ["山は雪に覆われていました。", "祖母のレシピはバニラを使います。", "電気自動車は人気です。", "図書館はセクションを拡張しました。", "竹は早く成長します。"],
        "subtraction_time": ["カエデは秋に色が変わります。", "宇宙望遠鏡は画像を撮影します。", "焼きたてのパンはいい香りです。", "テニスは協調性が必要です。", "イルカはクリック音で通信します。"],
        "duration_date": ["サハラには岩の形成があります。", "バイオリンには4本の弦があります。", "竹は非常に速く成長できます。", "シロナガスクジラは低い音を使います。", "新鮮なバジルは風味を加えます。"],
        "duration_time": ["ヒマワリは今年高く育ちました。", "いとこはバイオリンを弾きます。", "シロナガスクジラは重いです。", "レシピはバジルを使います。", "日本には多くの島があります。"],
        "recurrence_date": ["今日は空が青いです。", "隣人が自転車を買いました。", "焼きたてのパンはいい香りです。", "ペンギンは泳ぎが上手です。", "図書館には快適な椅子があります。"],
        "interval_date": ["オークの木は日陰を作ります。", "ウミガメは息を止められます。", "祖母のラザニアはチーズを使います。", "万里の長城は何年もかかりました。", "電気自動車は人気です。"],
        "day_of_week": ["海の波が岩に打ち寄せます。", "祖母は新鮮なバジルを使います。", "ソーラーパネルは日光が必要です。", "そのドキュメンタリーは魅力的でした。", "木製の椅子は塗装が必要です。"],
    },
    "ar_SA": {
        "addition_date": ["الحديقة تحتاج زهوراً جديدة.", "أخي اشترى دراجة نارية.", "الوصفة تتطلب السكر.", "الموسيقى الكلاسيكية تساعدني.", "المتحف يفتح الساعة التاسعة."],
        "subtraction_date": ["أحتاج حذاء جري جديد.", "المكتبة تغلق الساعة 8 مساءً.", "لوني المفضل هو البنفسجي.", "القهوة أفضل مع الحليب.", "الطيور تطير جنوباً في الشتاء."],
        "addition_time": ["الجبل كان مغطى بالثلج.", "وصفة جدتي تستخدم الفانيليا.", "السيارات الكهربائية شائعة.", "المكتبة وسعت قسمها.", "الخيزران ينمو بسرعة."],
        "subtraction_time": ["أشجار القيقب تتغير ألوانها في الخريف.", "التلسكوبات الفضائية تلتقط صوراً.", "الخبز الطازج رائحته رائعة.", "التنس يتطلب تنسيقاً.", "الدلافين تتواصل بالنقرات."],
        "duration_date": ["الصحراء فيها تشكيلات صخرية.", "الكمان له أربعة أوتار.", "الخيزران يمكن أن ينمو بسرعة.", "الحيتان الزرقاء تستخدم أصواتاً منخفضة.", "الريحان الطازج يضيف نكهة."],
        "duration_time": ["عباد الشمس نمت عالية هذا العام.", "ابن عمي يعزف الكمان.", "الحيتان الزرقاء تزن كثيراً.", "الوصفة تستخدم الريحان.", "اليابان فيها جزر كثيرة."],
        "recurrence_date": ["السماء تبدو زرقاء اليوم.", "جاري اشترى دراجة.", "الخبز الطازج رائحته رائعة.", "البطاريق سباحون ممتازون.", "المكتبة فيها كراسي مريحة."],
        "interval_date": ["شجرة البلوط توفر الظل.", "السلاحف البحرية تحبس أنفاسها.", "لازانيا جدتي تستخدم الجبن.", "سور الصين استغرق سنوات.", "السيارات الكهربائية شائعة."],
        "day_of_week": ["أمواج المحيط تضرب الصخور.", "جدتي تستخدم الريحان الطازج.", "الألواح الشمسية تحتاج ضوء الشمس.", "ذلك الوثائقي كان مذهلاً.", "الكرسي الخشبي يحتاج طلاء."],
    },
    "hi_IN": {
        "addition_date": ["बगीचे में नए फूल चाहिए।", "मेरे भाई ने मोटरसाइकिल खरीदी।", "रेसिपी में चीनी चाहिए।", "शास्त्रीय संगीत मदद करता है।", "संग्रहालय नौ बजे खुलता है।"],
        "subtraction_date": ["मुझे नए दौड़ने के जूते चाहिए।", "पुस्तकालय 8 बजे बंद होता है।", "मेरा पसंदीदा रंग बैंगनी है।", "कॉफी दूध के साथ अच्छी लगती है।", "पक्षी सर्दियों में दक्षिण की ओर उड़ते हैं।"],
        "addition_time": ["पहाड़ बर्फ से ढका था।", "दादी की रेसिपी में वनीला है।", "इलेक्ट्रिक कारें लोकप्रिय हैं।", "पुस्तकालय ने अपना खंड बढ़ाया।", "बांस तेजी से बढ़ता है।"],
        "subtraction_time": ["मेपल के पेड़ पतझड़ में रंग बदलते हैं।", "अंतरिक्ष दूरबीनें चित्र लेती हैं।", "ताजी रोटी अच्छी महकती है।", "टेनिस में समन्वय चाहिए।", "डॉल्फिन क्लिक से संवाद करती हैं।"],
        "duration_date": ["सहारा में चट्टान संरचनाएं हैं।", "वायलिन में चार तार होते हैं।", "बांस बहुत तेजी से बढ़ सकता है।", "नीली व्हेल कम आवाज का उपयोग करती है।", "ताजी तुलसी स्वाद जोड़ती है।"],
        "duration_time": ["सूरजमुखी इस साल लंबे हुए।", "मेरा चचेरा भाई वायलिन बजाता है।", "नीली व्हेल बहुत भारी होती है।", "रेसिपी में तुलसी है।", "जापान में कई द्वीप हैं।"],
        "recurrence_date": ["आज आसमान नीला है।", "मेरे पड़ोसी ने साइकिल खरीदी।", "ताजी रोटी अच्छी महकती है।", "पेंगुइन बढ़िया तैराक हैं।", "पुस्तकालय में आरामदायक कुर्सियां हैं।"],
        "interval_date": ["ओक का पेड़ छाया देता है।", "समुद्री कछुए सांस रोक सकते हैं।", "दादी की लसग्ना में पनीर है।", "चीन की दीवार में साल लगे।", "इलेक्ट्रिक कारें लोकप्रिय हैं।"],
        "day_of_week": ["समुद्र की लहरें चट्टानों से टकराती हैं।", "दादी ताजी तुलसी का उपयोग करती हैं।", "सोलर पैनल को धूप चाहिए।", "वह डॉक्यूमेंट्री आकर्षक थी।", "लकड़ी की कुर्सी को पेंट चाहिए।"],
    },
}


def get_insertion(language: str, task_type: str, similar: bool, seed: int = None) -> str:
    """Get a random insertion for the given language and task type.
    
    Args:
        language: Language code (e.g., 'en_US', 'es_ES')
        task_type: Task type key (e.g., 'addition_date', 'duration_time')
        similar: If True, returns a similar (time-related) insertion; if False, returns a dissimilar one
        seed: Optional random seed for reproducibility
        
    Returns:
        A random insertion string in the specified language
    """
    if seed is not None:
        random.seed(seed)
    
    insertions_dict = SIMILAR_INSERTIONS if similar else DISSIMILAR_INSERTIONS
    
    if language not in insertions_dict:
        language = "en_US"  # Fallback to English
    
    if task_type not in insertions_dict[language]:
        # Map task types to internal keys if needed
        task_type = task_type.replace("date_", "").replace("time_", "") + "_date"
        if task_type not in insertions_dict[language]:
            task_type = list(insertions_dict[language].keys())[0]
    
    return random.choice(insertions_dict[language][task_type])


def prepend_insertion(question: str, insertion: str) -> str:
    """Prepend an insertion to a question.
    
    Args:
        question: The original question text
        insertion: The insertion text to prepend
        
    Returns:
        The question with the insertion prepended, separated by a space
    """
    return f"{insertion} {question}"


def get_all_insertions(language: str, task_type: str, similar: bool) -> List[str]:
    """Get all insertions for the given language and task type.
    
    Args:
        language: Language code (e.g., 'en_US', 'es_ES')
        task_type: Task type key (e.g., 'addition_date', 'duration_time')
        similar: If True, returns similar insertions; if False, returns dissimilar ones
        
    Returns:
        List of all insertion strings for the specified language and task
    """
    insertions_dict = SIMILAR_INSERTIONS if similar else DISSIMILAR_INSERTIONS
    
    if language not in insertions_dict:
        language = "en_US"
    
    if task_type not in insertions_dict[language]:
        task_type = list(insertions_dict[language].keys())[0]
    
    return insertions_dict[language][task_type]


# Alias for backward compatibility
get_random_insertion = get_insertion
