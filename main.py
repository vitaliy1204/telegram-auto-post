
import datetime

# Приклад формування тексту
def get_post_text():
    дата = datetime.datetime.now().strftime("%Y-%m-%d")
    full_text = f"""*Запорізька гімназія №110*
Дата: {дата}
"""
    return full_text

if __name__ == "__main__":
    print(get_post_text())
