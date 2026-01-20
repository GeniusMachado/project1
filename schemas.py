class Student:
    def __init__(self, name: str, age: int, student_id: str):
        self.name = name
        self.age = age
        self.student_id = student_id

    def __repr__(self):
        return f"Student(name={self.name}, age={self.age}, student_id={self.student_id})"