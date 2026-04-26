from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
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
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=psycopg2.extras.RealDictCursor  # dict 형태로 반환 (pymysql의 DictCursor와 동일)
    )

class PostCreate(BaseModel):
    content: str

class PostUpdate(BaseModel):
    content: str

@app.get("/posts")
def get_posts():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
            posts = cursor.fetchall()
        return list(posts)
    finally:
        conn.close()

@app.post("/posts")
def create_post(body: PostCreate):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # RETURNING으로 삽입된 행 바로 반환 (LAST_INSERT_ID 대신)
            cursor.execute(
                "INSERT INTO posts (content) VALUES (%s) RETURNING *",
                (body.content,)
            )
            post = cursor.fetchone()
            conn.commit()
        return post
    finally:
        conn.close()

@app.patch("/posts/{post_id}")
def update_post(post_id: int, body: PostUpdate):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE posts SET content = %s WHERE id = %s RETURNING *",
                (body.content, post_id)
            )
            post = cursor.fetchone()
            conn.commit()
            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")
        return post
    finally:
        conn.close()

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM posts WHERE id = %s RETURNING id", (post_id,))
            deleted = cursor.fetchone()
            conn.commit()
            if deleted is None:
                raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "삭제 완료"}
    finally:
        conn.close()