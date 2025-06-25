import os
from dotenv import load_dotenv
from agents.math import math_tutor
from agents.arabic import arabic_tutor
from agents.english import english_tutor

# Load environment variables
load_dotenv()

def ask(subject, question):
    """
    Route questions to the appropriate subject tutor
    
    Args:
        subject (str): The subject name (math, arabic, english)
        question (str): The student's question
    
    Returns:
        str: The tutor's response
    """
    try:
        if subject.lower() == "math":
            response = math_tutor.start(question)
            return response if response else "عذراً، لم أتمكن من الإجابة على سؤالك."
        elif subject.lower() == "arabic":
            response = arabic_tutor.start(question)
            return response if response else "عذراً، لم أتمكن من الإجابة على سؤالك."
        elif subject.lower() == "english":
            response = english_tutor.start(question)
            return response if response else "عذراً، لم أتمكن من الإجابة على سؤالك."
        else:
            return "المادة غير متوفرة. المواد المتاحة: math, arabic, english"
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

def main():
    """Main interactive loop"""
    print("🎓 مرحباً بك في نظام التوجيهي الذكي")
    print("📚 المواد المتاحة: math, arabic, english")
    print("❌ اكتب 'exit' للخروج\n")
    
    while True:
        try:
            subject = input("📖 المادة (Subject): ").strip()
            if subject.lower() == 'exit':
                print("👋 وداعاً!")
                break
                
            if not subject:
                print("⚠️ يرجى إدخال اسم المادة")
                continue
                
            question = input("❓ سؤالك (Question): ").strip()
            if not question:
                print("⚠️ يرجى إدخال السؤال")
                continue
                
            print("\n🤖 الإجابة:")
            print("-" * 50)
            response = ask(subject, question)
            print(response)
            print("-" * 50)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 وداعاً!")
            break
        except Exception as e:
            print(f"❌ خطأ: {str(e)}")
            print("يرجى المحاولة مرة أخرى\n")

if __name__ == "__main__":
    main()