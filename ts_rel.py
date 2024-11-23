import os

# 假设文件在同一目录下
file1 = "1.md"  # 或者 "1.md"，确保路径分隔符一致
file2 = r"1\240303102___In_Dialogues_We_Learn___Towards_Personalized_Dialogue_Without___Pre-defined_Profiles_through_In-Dialogue_Learning.pdf"
print(file2)
print("good", os.path.dirname(file1))

# 获取相对路径
relative_path = os.path.relpath(file2, file1)
print(relative_path)

relative_path = os.path.relpath(file2, os.path.dirname(file1))

print(relative_path)
