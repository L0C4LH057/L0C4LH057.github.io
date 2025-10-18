
import google.generativeai as genai



API_KEY = "AIzaSyDroBpDUyxdb0l2CFYabQE3rNX09yivl0I"
# -----------------------------------

genai.configure(api_key=API_KEY)
for m in genai.list_models():
    print(m.name)



