"""Question templates for all 9 tasks in 10 languages.

Templates are parameterized with placeholders for temporal values.
Based on Table 2 of the paper and translations in the Experimental Plan.
"""

from typing import Dict

# English templates
QUESTION_TEMPLATES_EN = {
    "addition_date": "Today is {current_date}, what is the date going to be in {days_to_add} {day_or_days}?",
    "subtraction_date": "Today is {current_date}, what was the date {days_to_subtract} {day_or_days} ago?",
    "addition_time": "It is now {current_time}, what will the time be in {hours_to_add} {hour_or_hours} and {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "It is now {current_time}, what was the time {hours_to_subtract} {hour_or_hours} and {minutes_to_subtract} {minute_or_minutes} ago?",
    "day_of_week": "What day of the week (e.g., Monday, Tuesday, ...) is {date}?",
    "recurrence_date": "Today is {current_date}, and I have a recurrence every {recurrence_days} {day_or_days}. Without counting today, what is the date of the {occurrence} occurrence?",
    "duration_date": "How many day(s) (e.g., 5, 9) have passed between {start_date} and {end_date}?",
    "duration_time": "If I looked at the clock at {start_time} and now it is {end_time}, how many minutes (e.g., 15, 23) have gone by?",
    "interval_date": "If today is {current_date}, what are the dates for the start and end of next week, assuming Monday is the first day of the week?",
}

# Spanish templates
QUESTION_TEMPLATES_ES = {
    "addition_date": "Hoy es {current_date}, ¿cuál será la fecha dentro de {days_to_add} {day_or_days}?",
    "subtraction_date": "Hoy es {current_date}, ¿cuál era la fecha hace {days_to_subtract} {day_or_days}?",
    "addition_time": "Ahora son las {current_time}, ¿qué hora será dentro de {hours_to_add} {hour_or_hours} y {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "Ahora son las {current_time}, ¿qué hora era hace {hours_to_subtract} {hour_or_hours} y {minutes_to_subtract} {minute_or_minutes}?",
    "duration_date": "¿Cuántos días (ej. 5, 9) han pasado entre el {start_date} y el {end_date}?",
    "duration_time": "Si miré el reloj a las {start_time} y ahora son las {end_time}, ¿cuántos minutos (ej. 15, 23) han pasado?",
    "recurrence_date": "Hoy es {current_date} y tengo un recordatorio cada {recurrence_days} {day_or_days}. Sin contar el día de hoy, ¿cuál es la fecha de la {occurrence}ª ocurrencia?",
    "interval_date": "Si hoy es {current_date}, ¿cuál es la fecha en la que comienza y termina la semana siguiente, teniendo en cuenta que el lunes es el primer día de la semana?",
    "day_of_week": "¿Qué día de la semana (ej., lunes, martes, etc.) es {date}?",
}

# Italian templates
QUESTION_TEMPLATES_IT = {
    "addition_date": "Oggi è {current_date}, che data sarà tra {days_to_add} {day_or_days}?",
    "subtraction_date": "Oggi è il {current_date}, qual era la data {days_to_subtract} {day_or_days} fa?",
    "addition_time": "Adesso sono le {current_time}, che ora sarà tra {hours_to_add} {hour_or_hours} e {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "Adesso sono le {current_time}, che ora era {hours_to_subtract} {hour_or_hours} e {minutes_to_subtract} {minute_or_minutes} fa?",
    "day_of_week": "Che giorno della settimana (es., lunedì, martedì, ...) è il {date}?",
    "recurrence_date": "Oggi è {current_date}, e ho una ricorrenza ogni {recurrence_days} {day_or_days}. Senza contare oggi, qual è la data della {occurrence}ª ricorrenza?",
    "duration_date": "Quanti giorni (es. 5, 9) sono passati tra {start_date} e {end_date}?",
    "duration_time": "Se ho guardato l'orologio alle {start_time} e ora sono le {end_time}, quanti minuti (es. 15, 23) sono trascorsi?",
    "interval_date": "Se oggi è {current_date}, quali sono le date di inizio e fine della prossima settimana, assumendo che lunedì sia il primo giorno della settimana?",
}

# French templates
QUESTION_TEMPLATES_FR = {
    "addition_date": "Aujourd'hui c'est le {current_date}, quelle sera la date dans {days_to_add} {day_or_days}?",
    "subtraction_date": "Aujourd'hui, c'est le {current_date}, quelle était la date il y a {days_to_subtract} {day_or_days}?",
    "addition_time": "Il est actuellement {current_time}, quelle heure sera-t-il dans {hours_to_add} {hour_or_hours} et {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "Il est maintenant {current_time}, quelle heure était-il il y a {hours_to_subtract} {hour_or_hours} et {minutes_to_subtract} {minute_or_minutes}?",
    "day_of_week": "Quel jour de la semaine (ex., Lundi, Mardi, ...) est le {date}?",
    "recurrence_date": "Aujourd'hui c'est le {current_date}, et j'ai une récurrence tous les {recurrence_days} {day_or_days}. Sans compter aujourd'hui, quelle est la date de la {occurrence}ème récurrence?",
    "duration_date": "Combien de jours (ex. 5, 9) se sont écoulés entre le {start_date} et le {end_date}?",
    "duration_time": "Si j'ai regardé l'horloge à {start_time} et qu'il est maintenant {end_time}, combien de minutes (ex. 15, 23) se sont écoulées?",
    "interval_date": "Si aujourd'hui c'est le {current_date}, quelles sont les dates de début et de fin de la semaine prochaine, en supposant que lundi est le premier jour de la semaine?",
}

# German templates
QUESTION_TEMPLATES_DE = {
    "addition_date": "Heute ist {current_date}, welches Datum wird in {days_to_add} {day_or_days} sein?",
    "subtraction_date": "Heute ist der {current_date}, welches Datum war vor {days_to_subtract} {day_or_days}?",
    "addition_time": "Es ist jetzt {current_time} Uhr, wie spät wird es in {hours_to_add} {hour_or_hours} und {minutes_to_add} {minute_or_minutes} sein?",
    "subtraction_time": "Es ist jetzt {current_time} Uhr, wie spät war es vor {hours_to_subtract} {hour_or_hours} und {minutes_to_subtract} {minute_or_minutes}?",
    "day_of_week": "Welcher Wochentag (z.B. Montag, Dienstag, ...) ist der {date}?",
    "recurrence_date": "Heute ist {current_date}, und ich habe eine Wiederholung alle {recurrence_days} {day_or_days}. Ohne heute mitzuzählen, was ist das Datum der {occurrence}. Wiederholung?",
    "duration_date": "Wie viele Tage (z.B. 5, 9) sind zwischen {start_date} und {end_date} vergangen?",
    "duration_time": "Wenn ich um {start_time} Uhr auf die Uhr geschaut habe und es jetzt {end_time} Uhr ist, wie viele Minuten (z.B. 15, 23) sind vergangen?",
    "interval_date": "Wenn heute {current_date} ist, was sind die Daten für den Beginn und das Ende der nächsten Woche, wenn man davon ausgeht, dass Montag der erste Tag der Woche ist?",
}

# Portuguese templates
QUESTION_TEMPLATES_PT = {
    "addition_date": "Hoje é {current_date}, qual será a data daqui a {days_to_add} {day_or_days}?",
    "subtraction_date": "Hoje é {current_date}, qual era a data há {days_to_subtract} {day_or_days} atrás?",
    "addition_time": "Agora são {current_time}, que horas serão daqui a {hours_to_add} {hour_or_hours} e {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "Agora são {current_time}, que horas eram há {hours_to_subtract} {hour_or_hours} e {minutes_to_subtract} {minute_or_minutes} atrás?",
    "day_of_week": "Que dia da semana (ex., Segunda-feira, Terça-feira, ...) é {date}?",
    "recurrence_date": "Hoje é {current_date}, e tenho uma recorrência a cada {recurrence_days} {day_or_days}. Sem contar hoje, qual é a data da {occurrence}ª recorrência?",
    "duration_date": "Quantos dias (ex. 5, 9) se passaram entre {start_date} e {end_date}?",
    "duration_time": "Se eu olhei para o relógio às {start_time} e agora são {end_time}, quantos minutos (ex. 15, 23) se passaram?",
    "interval_date": "Se hoje é {current_date}, quais são as datas de início e fim da próxima semana, assumindo que segunda-feira é o primeiro dia da semana?",
}

# Dutch templates
QUESTION_TEMPLATES_NL = {
    "addition_date": "Vandaag is {current_date}, wat zal de datum zijn over {days_to_add} {day_or_days}?",
    "subtraction_date": "Vandaag is het {current_date}, wat was de datum {days_to_subtract} {day_or_days} geleden?",
    "addition_time": "Het is nu {current_time}, hoe laat zal het zijn over {hours_to_add} {hour_or_hours} en {minutes_to_add} {minute_or_minutes}?",
    "subtraction_time": "Het is nu {current_time} uur, hoe laat was het {hours_to_subtract} {hour_or_hours} en {minutes_to_subtract} {minute_or_minutes} geleden?",
    "day_of_week": "Welke dag van de week (bijv. maandag, dinsdag, ...) is {date}?",
    "recurrence_date": "Vandaag is {current_date}, en ik heb een herhaling elke {recurrence_days} {day_or_days}. Zonder vandaag mee te tellen, wat is de datum van de {occurrence}e herhaling?",
    "duration_date": "Hoeveel dagen (bijv. 5, 9) zijn er verstreken tussen {start_date} en {end_date}?",
    "duration_time": "Als ik om {start_time} op de klok keek en het is nu {end_time}, hoeveel minuten (bijv. 15, 23) zijn er voorbijgegaan?",
    "interval_date": "Als vandaag {current_date} is, wat zijn de begin- en einddatums van volgende week, ervan uitgaande dat maandag de eerste dag van de week is?",
}

# Japanese templates
QUESTION_TEMPLATES_JA = {
    "addition_date": "今日は{current_date}です。{days_to_add}日後は何日になりますか？",
    "subtraction_date": "今日は{current_date}ですが、{days_to_subtract}日前は何日でしたか？",
    "addition_time": "今{current_time}です。{hours_to_add}時間{minutes_to_add}分後は何時ですか？",
    "subtraction_time": "今は{current_time}ですが、{hours_to_subtract}時間{minutes_to_subtract}分前は何時でしたか？",
    "day_of_week": "{date}は何曜日（例：月曜日、火曜日、...）ですか？",
    "recurrence_date": "今日は{current_date}で、{recurrence_days}日おきに繰り返すよう設定されているものがあります。今日を除いて、{occurrence}回目の繰り返しの日付は何ですか？",
    "duration_date": "{start_date}から{end_date}までの間に何日（例：5、9）経過していますか？",
    "duration_time": "{start_time}に時計を見て、今{end_time}だとすると、何分（例：15、23）経過しましたか？",
    "interval_date": "今日が{current_date}だとして、月曜日を週の最初の日と仮定すると、来週の開始日と終了日は何日ですか？",
}

# Arabic templates
QUESTION_TEMPLATES_AR = {
    "addition_date": "اليوم هو {current_date}. ما هو التاريخ بعد {days_to_add} أيام؟",
    "subtraction_date": "تاريخ اليوم هو {current_date}. كم كان التاريخ قبل {days_to_subtract} أيام؟",
    "addition_time": "الساعة الآن {current_time}. كم الساعة بعد {hours_to_add} ساعة و{minutes_to_add} دقيقة؟",
    "subtraction_time": "الآن الساعة {current_time}. كم كانت الساعة قبل {hours_to_subtract} ساعات و{minutes_to_subtract} دقيقة؟",
    "duration_date": "كم يوماً (مثل 5، 9) مر بين {start_date} و{end_date}؟",
    "duration_time": "إذا نظرت إلى الساعة في {start_time} والآن هي {end_time}، كم دقيقة (مثل 15، 23) مرت؟",
    "recurrence_date": "تاريخ اليوم هو {current_date}. عندي موعد يتكرر كل {recurrence_days} أيام. لو لم نحسب اليوم، ما هو تاريخ الموعد {occurrence}؟",
    "interval_date": "إذا كان اليوم هو {current_date}، فلنفرض أن الاثنين هو أول يوم في الأسبوع، ما هو تاريخ بداية ونهاية الأسبوع القادم؟",
    "day_of_week": "أي يوم من أيام الأسبوع (مثل الاثنين، الثلاثاء، ...) سيكون التاريخ الموافق {date}؟",
}

# Hindi templates
QUESTION_TEMPLATES_HI = {
    "addition_date": "आज {current_date} है, {days_to_add} दिनों में तिथि क्या होगी?",
    "subtraction_date": "आज {current_date} है, {days_to_subtract} दिन पहले क्या तारीख थी?",
    "addition_time": "अभी {current_time} बजे हैं, {hours_to_add} घंटे और {minutes_to_add} मिनट बाद समय क्या होगा?",
    "subtraction_time": "अभी {current_time} बजे हैं, {hours_to_subtract} घंटे और {minutes_to_subtract} मिनट पहले क्या समय था?",
    "duration_date": "{start_date} और {end_date} के बीच कितने दिन (जैसे 5, 9) बीत चुके हैं?",
    "duration_time": "अगर मैंने {start_time} पर घड़ी देखी और अब {end_time} है, तो कितने मिनट (जैसे 15, 23) बीत चुके हैं?",
    "recurrence_date": "आज {current_date} है, और मेरे पास हर {recurrence_days} दिनों पर एक पुनरावृत्ति है। आज को छोड़कर, {occurrence}वीं आवृत्ति की तिथि क्या है?",
    "interval_date": "यदि आज {current_date} है, तो अगले सप्ताह की शुरुआत और अंत की तिथियां क्या हैं, यह मानते हुए कि सोमवार सप्ताह का पहला दिन है?",
    "day_of_week": "{date} सप्ताह का कौन सा दिन (जैसे सोमवार, मंगलवार, ...) है?",
}

# Main template dictionary keyed by language code
QUESTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "en_US": QUESTION_TEMPLATES_EN,
    "es_ES": QUESTION_TEMPLATES_ES,
    "de_DE": QUESTION_TEMPLATES_DE,
    "fr_FR": QUESTION_TEMPLATES_FR,
    "hi_IN": QUESTION_TEMPLATES_HI,
    "it_IT": QUESTION_TEMPLATES_IT,
    "ja_JP": QUESTION_TEMPLATES_JA,
    "pt_BR": QUESTION_TEMPLATES_PT,
    "ar_SA": QUESTION_TEMPLATES_AR,
    "nl_NL": QUESTION_TEMPLATES_NL,
}


def get_question_template(language_code: str, task_key: str) -> str:
    """Get the question template for a specific language and task.
    
    Args:
        language_code: Language code (e.g., "en_US")
        task_key: Template key (e.g., "addition_date", "day_of_week")
        
    Returns:
        Question template string with placeholders
        
    Raises:
        ValueError: If language or task key is not valid
    """
    if language_code not in QUESTION_TEMPLATES:
        valid_langs = ", ".join(QUESTION_TEMPLATES.keys())
        raise ValueError(f"Unknown language code: {language_code}. Valid: {valid_langs}")
    
    templates = QUESTION_TEMPLATES[language_code]
    if task_key not in templates:
        valid_tasks = ", ".join(templates.keys())
        raise ValueError(f"Unknown task key: {task_key}. Valid: {valid_tasks}")
    
    return templates[task_key]
