import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def connect_to_database():
    try:
        connection = psycopg2.connect(host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
                                      user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
        return connection
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)


def create_position_table():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Office_Positions (
                          id SERIAL PRIMARY KEY,
                          lavozim VARCHAR(255) NOT NULL)
                          ''')
        connection.commit()
        connection.close()
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)


def create_employee_table():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Employees (
                          id SERIAL PRIMARY KEY,
                          ism VARCHAR(255) NOT NULL,
                          familiya VARCHAR(255) NOT NULL,
                          tugilgan_kun VARCHAR(10) NOT NULL,
                          lavozim VARCHAR(255) NOT NULL,  -- Add the "lavozim" column
                          rasm VARCHAR(255))  -- Change data type to VARCHAR
                          ''')
        connection.commit()
        connection.close()
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)


def add_employee(ism, familiya, tugilgan_kun, lavozim, rasm):  # Change image_path to image_url
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO Employees (ism, familiya, tugilgan_kun, lavozim, rasm)
                          VALUES (%s, %s, %s, %s, %s)''', (ism, familiya, tugilgan_kun, lavozim, rasm))
        connection.commit()
        connection.close()
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)


def get_employees_by_birthdate(birthdate):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Employees WHERE EXTRACT(MONTH FROM tugilgan_kun) = %s AND EXTRACT(DAY FROM tugilgan_kun) = %s", (birthdate.month, birthdate.day))
        employees = cursor.fetchall()
        connection.close()
        return employees
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)


def get_position_name(lavozim):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT lavozim FROM Office_Positions WHERE id = %s", (lavozim,))
        position = cursor.fetchone()
        connection.close()
        if position:
            return position[0]
        else:
            return None
    except psycopg2.Error as e:
        print("Xatolik yuz berdi: ", e)
        return None


create_employee_table()
create_position_table()
