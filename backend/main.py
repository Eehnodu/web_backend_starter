from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=4000,
        ssl={"ssl_mode": "VERIFY_IDENTITY"},
        cursorclass=pymysql.cursors.DictCursor,
    )

class PostCreate(BaseModel):
    content: str

class PostUpdate(BaseModel):
    content: str

# GET /posts - 전체 조회
@app.get("/posts")
def get_posts():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
            posts = cursor.fetchall()
        return posts
    finally:
        conn.close()

# POST /posts - 생성
@app.post("/posts")
def create_post(body: PostCreate):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO posts (content) VALUES (%s)", (body.content,))
            conn.commit()
            cursor.execute("SELECT * FROM posts WHERE id = LAST_INSERT_ID()")
            post = cursor.fetchone()
        return post
    finally:
        conn.close()

# PATCH /posts/{id} - 수정
@app.patch("/posts/{post_id}")
def update_post(post_id: int, body: PostUpdate):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE posts SET content = %s WHERE id = %s", (body.content, post_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Post not found")
            cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
            post = cursor.fetchone()
        return post
    finally:
        conn.close()

# DELETE /posts/{id} - 삭제
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "삭제 완료"}
    finally:
        conn.close()