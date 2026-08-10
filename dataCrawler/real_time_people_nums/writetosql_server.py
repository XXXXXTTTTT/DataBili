import pymysql
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import database_config

def insert_bilibili_data(data, host=None, port=None, user=None, password=None, database=None):
    """
    插入B站视频数据到数据库
    
    Args:
        data: 包含timestamp、formatted_time和data字段的字典
        host, port, user, password, database: 数据库连接参数
        
    Returns:
        bool: 插入是否成功
    """
    connection = None
    try:
        # 连接数据库
        config = database_config()
        connection = pymysql.connect(
            host=host or config["host"],
            port=port or config["port"],
            user=user or config["user"],
            password=password if password is not None else config["password"],
            database=database or config["database"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 检查表是否存在，不存在则创建
            cursor.execute("SHOW TABLES LIKE 'bilibili_hot_videos_server'")
            if not cursor.fetchone():
                create_table_sql = """
                CREATE TABLE bilibili_hot_videos_server (
                    timestamp BIGINT NOT NULL,
                    aid BIGINT NOT NULL,
                    videos INT,
                    tid INT,
                    tname VARCHAR(50),
                    copyright TINYINT,
                    pic VARCHAR(500),
                    title TEXT,
                    pubdate BIGINT,
                    ctime BIGINT,
                    `desc` TEXT,
                    state INT,
                    duration INT,
                    tnamev2 VARCHAR(50),
                    pid_name_v2 VARCHAR(50),
                    short_link_v2 VARCHAR(200),
                    dynamic TEXT,
                    stat_view INT,
                    stat_danmaku INT,
                    stat_reply INT,
                    stat_favorite INT,
                    stat_coin INT,
                    stat_share INT,
                    stat_now_rank INT,
                    stat_his_rank INT,
                    stat_like INT,
                    stat_dislike INT,
                    stat_vt INT,
                    stat_vv INT,
                    stat_fav_g INT,
                    stat_like_g INT,
                    owner_mid BIGINT,
                    owner_name VARCHAR(100),
                    owner_face VARCHAR(500),
                    tags TEXT,
                    real_time_all VARCHAR(20),
                    real_time_web VARCHAR(20),
                    formatted_time VARCHAR(30),
                    PRIMARY KEY (timestamp, aid),
                    INDEX idx_aid (aid),
                    INDEX idx_pubdate (pubdate),
                    INDEX idx_owner_mid (owner_mid),
                    INDEX idx_stat_view (stat_view),
                    INDEX idx_real_time_all (real_time_all),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
                cursor.execute(create_table_sql)
                print("表 bilibili_hot_videos_server 创建成功")
            else:
                # 检查是否需要添加新字段
                cursor.execute("SHOW COLUMNS FROM bilibili_hot_videos_server LIKE 'real_time_all'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE bilibili_hot_videos_server ADD COLUMN real_time_all VARCHAR(20) AFTER tags")
                    print("添加字段 real_time_all 成功")
                
                cursor.execute("SHOW COLUMNS FROM bilibili_hot_videos_server LIKE 'real_time_web'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE bilibili_hot_videos_server ADD COLUMN real_time_web VARCHAR(20) AFTER real_time_all")
                    cursor.execute("ALTER TABLE bilibili_hot_videos_server ADD INDEX idx_real_time_all (real_time_all)")
                    print("添加字段 real_time_web 成功")
            
            # 获取全局timestamp和formatted_time
            global_timestamp = data.get('timestamp')
            global_formatted_time = data.get('formatted_time')
            video_list = data.get('data', [])
            
            if not video_list:
                print("没有视频数据需要插入")
                return False
            
            # 插入数据 - 添加实时在线人数字段
            insert_sql = """
            INSERT INTO bilibili_hot_videos_server (
                timestamp, aid, videos, tid, tname, copyright, pic, title, pubdate, ctime,
                `desc`, state, duration, tnamev2, pid_name_v2, short_link_v2, dynamic,
                stat_view, stat_danmaku, stat_reply, stat_favorite, stat_coin, stat_share,
                stat_now_rank, stat_his_rank, stat_like, stat_dislike, stat_vt, stat_vv,
                stat_fav_g, stat_like_g, owner_mid, owner_name, owner_face, tags, 
                real_time_all, real_time_web, formatted_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            success_count = 0
            for video in video_list:
                try:
                    # 使用视频自身的timestamp，如果没有则使用全局timestamp
                    video_timestamp = video.get('timestamp', global_timestamp)
                    video_formatted_time = video.get('formatted_time', global_formatted_time)
                    
                    # 处理tags字段 - 如果是列表则转换为JSON字符串
                    tags_value = video.get('tags')
                    if isinstance(tags_value, list):
                        import json
                        tags_value = json.dumps(tags_value, ensure_ascii=False)
                    
                    values = (
                        video_timestamp,
                        video.get('aid'),
                        video.get('videos'),
                        video.get('tid'),
                        video.get('tname'),
                        video.get('copyright'),
                        video.get('pic'),
                        video.get('title'),
                        video.get('pubdate'),
                        video.get('ctime'),
                        video.get('desc'),
                        video.get('state'),
                        video.get('duration'),
                        video.get('tnamev2'),
                        video.get('pid_name_v2'),
                        video.get('short_link_v2'),
                        video.get('dynamic'),
                        video.get('stat_view'),
                        video.get('stat_danmaku'),
                        video.get('stat_reply'),
                        video.get('stat_favorite'),
                        video.get('stat_coin'),
                        video.get('stat_share'),
                        video.get('stat_now_rank'),
                        video.get('stat_his_rank'),
                        video.get('stat_like'),
                        video.get('stat_dislike'),
                        video.get('stat_vt'),
                        video.get('stat_vv'),
                        video.get('stat_fav_g'),
                        video.get('stat_like_g'),
                        video.get('owner_mid'),
                        video.get('owner_name'),
                        video.get('owner_face'),
                        tags_value,
                        video.get('real_time_all', '0'),  # 新增：实时总在线人数
                        video.get('real_time_web', '0'),  # 新增：实时网页端在线人数
                        video_formatted_time
                    )
                    
                    cursor.execute(insert_sql, values)
                    success_count += 1
                    
                except Exception as e:
                    print(f"插入视频 aid={video.get('aid')} 失败: {e}")
            
            connection.commit()
            print(f"成功插入 {success_count} 条视频记录")
            return success_count > 0
            
    except Exception as e:
        print(f"数据库操作失败: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    insert_bilibili_data({})
