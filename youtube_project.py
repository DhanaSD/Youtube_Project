#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Importing Necessary Libraries
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import seaborn as sns
import re
import pymongo
import pymysql
import plotly.express as px

#-----------------------------------------------------------------------------------------------------

#Access YouTube API:
api_key='AIzaSyAxKLhPASzg6p7l1W1_R8ayFKeKdFe7zPg'
youtube=build('youtube','v3',developerKey=api_key)

#-----------------------------------------------------------------------------------------------------

#Data Collection
st.markdown(
    f"<h1 style='color:#F24C3D; font-size: 24px;'>YOUTUBE DATA HARVESTING</h1>",
    unsafe_allow_html=True,)

st.markdown(
    f"<h1 style='color:#2F4858; font-size: 20px;'>DATA COLLECTION & STORE IT IN A MONGODB DATA LAKE</h1>",
    unsafe_allow_html=True,)

channel_id=st.text_input(':grey[Enter a channel_id:]')
submit=st.button(':black[Search]')

 
#Function To get Channel Data:
def get_channel_data(youtube, channel_id): 
    try:        
        request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=channel_id)
        response = request.execute()    
        data =dict(channel_id=response['items'][0]['id'],
                   channel_name= response['items'][0]['snippet']['title'],
                   channel_description= response['items'][0]['snippet']['description'],
                   subscriber_count = response['items'][0]['statistics']['subscriberCount'],
                  video_count = response['items'][0]['statistics']['videoCount'],
                  view_count = response['items'][0]['statistics']['viewCount'],                     
                 playlist_id= response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
        return data 
    except:
        print(" ")    
channel_data= get_channel_data(youtube, channel_id) 
 
#Function To get Video_ids:
try:
   playlist_id=channel_data['playlist_id']  
except:
    print(" ")   
def get_video_ids(youtube,playlist_id):
  try:
     request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50)                   
     response = request.execute()
     video_ids=[]
     for i in range(len(response["items"])):
        video_ids.append(response['items'][i]["contentDetails"]["videoId"])
     next_page_token=response.get('nextPageToken')
     more_pages=True
     while more_pages: 
        if next_page_token is None:
            more_pages=False
        else:  
            request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token) 
            response = request.execute()
            for i in range(len(response["items"])):
                video_ids.append(response['items'][i]["contentDetails"]["videoId"])
        next_page_token=response.get('nextPageToken')              
     return video_ids 
  except:
      print("")
 
 #Function To get Video Data:
try:
    video_ids=get_video_ids(youtube,playlist_id)  
except:
    print("")    
def get_video_data(youtube,video_ids):
    try:       
        video_data=[]
        request = youtube.videos().list(
                  part="snippet,contentDetails,statistics",
                  id=','.join(video_ids[:50]))        
        response = request.execute()
        for i in range(len(response['items'])):
            data = dict(video_id = response['items'][i]['id'],
                    channel_id = response['items'][i]['snippet']['channelId'],
                    video_name = response['items'][i]['snippet']['title'],
                    video_description = response['items'][i]['snippet']['description'],
                    published_date = response['items'][i]['snippet']['publishedAt'],
                    view_count = response['items'][i]['statistics']['viewCount'],
                    like_count = response['items'][i]['statistics']['likeCount'],
                    favourite_count = response['items'][i]['statistics']['favoriteCount'],
                    comment_count = response['items'][i]['statistics']['commentCount'],
                    duration = response['items'][i]['contentDetails']['duration'],
                    caption_status = response['items'][i]['contentDetails']['caption'])                    
            video_data.append(data)            
        return video_data
    except:
        all_data=[]
        request = youtube.videos().list(
               part="snippet,contentDetails,statistics",
              id=','.join(video_ids[:50]))
        response = request.execute()
        for i in range(len(response['items'])):
            data = dict(video_id = response['items'][i]['id'],
                    channel_id = response['items'][i]['snippet']['channelId'],
                    video_name = response['items'][i]['snippet']['title'],
                    video_description = response['items'][i]['snippet']['description'],
                    published_date = response['items'][i]['snippet']['publishedAt'],
                    view_count = response['items'][i]['statistics']['viewCount'],
                    like_count =-1,
                    favourite_count = response['items'][i]['statistics']['favoriteCount'],
                    comment_count =-1,
                    duration = response['items'][i]['contentDetails']['duration'],
                    caption_status = response['items'][i]['contentDetails']['caption'])
        all_data.append(data)
        return video_data
try:        
   video_dict= get_video_data(youtube,video_ids)   
except:
    print("")       

 #Fuction to convert duration column into seconds
duration='PT23M55S'
def parse_duration(duration):
    # (\d+) - one or more digits.
    # ? - makes the preceding element or group in the pattern optional
    # PT,M,S are alphabets as mentioned in the expression inbetween which digits are present
    # PT(hrs)H(mins)M(secs)S
    duration_regex = r'PT((\d+)H)?((\d+)M)?((\d+)S)?'
    matches = re.match(duration_regex, duration)
    # Period of Time timestamp(string) to seconds(int)
    if matches:
        # In this pattern, the first group starts with "(", so it's the number 1.
        # The second group starts with "((", so it's number 2
        # The third group starts after ? & so, it goes on
        hours = int(matches.group(2) or 0)
        minutes = int(matches.group(4) or 0)
        seconds = int(matches.group(6) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
        
 
#Function To get Playlist Data:
def get_playlist_data(youtube,channel_id): 
    try:      
       playlist_data=[]
       request = youtube.playlists().list(
        part="snippet,contentDetails",
        channelId=channel_id,
        maxResults=50)    
       response = request.execute()
       for i in range(len(response['items'])):
           data = dict(playlist_id = response['items'][i]['id'],
                    channel_id = response['items'][i]['snippet']['channelId'],
                    playlist_name = response['items'][i]['snippet']['title'])
           playlist_data.append(data)            
       return playlist_data  
    except:
        print("")
       
playlist_dict=get_playlist_data(youtube,channel_id)

#Function To Get Comment Data:
def get_comment_data(youtube,channel_id): 
    try:       
        comment_data=[]
        request = youtube.commentThreads().list(
        part="snippet,replies",
        allThreadsRelatedToChannelId=channel_id)
        response = request.execute()  

        for i in range(len(response['items'])):
            data = dict(comment_id = response['items'][i]['id'],
                    video_id = response['items'][i]['snippet']['videoId'],
                    channel_id = response['items'][i]['snippet']['channelId'],
                    comment_text= response['items'][i]['snippet']['topLevelComment']['snippet']['textOriginal'],
                    comment_author = response['items'][i]['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    comment_published_date = response['items'][i]['snippet']['topLevelComment']['snippet']['publishedAt'])
            comment_data.append(data)          
        return comment_data
    except:
        print("")
comment_dict=get_comment_data(youtube,channel_id)

if __name__ == "__main__":
  try:
    get_channel_data(youtube,channel_id)
    get_video_ids(youtube,playlist_id)
    get_video_data(youtube,video_ids)
    get_playlist_data(youtube,channel_id)
    get_comment_data(youtube,channel_id)
    parse_duration(duration)
  except:
      print(" ")  

if submit:  
  
  video_data={i['video_id']:i for i in video_dict}
  playlist_data={i['playlist_id']:i for i in playlist_dict}
  comment_data={i['comment_id']:i for i in comment_dict}
 
#Data Migrated to MongoDB
 #Connect to MongoDB with Localhost:  
  client = pymongo.MongoClient('mongodb://localhost:27017')

 #Create a DataBase or Used Existed One:  
  mydb = client["youtube"]

#Create Collection and Insert Data
  information = mydb.channel_data
  try:
     mydb.channel_data.create_index([("channel_id", 1)], unique=True)
     information.insert_one(channel_data)
     st.markdown(
        f"<h1 style='color:#539165; font-size: 24px;'>Data sucessfully Migrated to MongoDB </h1>",
       unsafe_allow_html=True,)
 
  except:
     st.markdown(
    f"<h1 style='color:#D83F31; font-size: 18px;'>Duplicate Entry, This Entry cannot be Migrated to MongoDB </h1>",
    unsafe_allow_html=True,)
 
 
  information = mydb.video_data
  try:
      mydb.video_data.create_index([("video_id", 1)], unique=True)
      information.insert_one(video_data) 
  except:
     print("") 

  information = mydb.playlist_data
  try:
      mydb.playlist_data.create_index([("playlist_id", 1)], unique=True)
      information.insert_one(playlist_data)
  except:
     print("") 

  information = mydb.comment_data
  try:
      mydb.comment_data.create_index([("comment_id", 1)], unique=True)
      information.insert_one(comment_data) 
  except:
     print("")
  col1,col2,col3,col4=st.columns(4)
  with col1:
     st.text("Channel_Details")
     st.write(channel_data)
  with col2:
     st.text("Video_Details")
     st.write(video_dict)
  with col3:
     st.text("Playlist_Details")
     st.write(playlist_dict) 
  with col4:
     st.text("Comment_Details")
     st.write(comment_dict)
try:
 client = pymongo.MongoClient('mongodb://localhost:27017')
 mydb = client["youtube"]
 def channel_names():
    ch_names=[]
    for i in mydb.channel_data.find():
        ch_names.append(i["channel_name"])
    return ch_names  
 ch_name=channel_names()

 st.markdown(
    f"<h1 style='color:#2F4858; font-size: 20px;'>DATA MIGRATION</h1>",
    unsafe_allow_html=True,)

 user_channel_name= st.selectbox(':grey[**Select channel name:**]', options =ch_name, key='ch_name')
 st.write('''Migrate to MySQL database from MongoDB database to click below **:blue['Migrate to MySQL']**.''')
 migrate = st.button('**Migrate to MySQL**')  
 if migrate:

    def channel_id(user_channel_name):
     for i in mydb.channel_data.find():
        if i["channel_name"]==user_channel_name:
            ch_id=i["channel_id"]
     return ch_id
    
    user_channel_id=channel_id(user_channel_name)    
    channel_details=get_channel_data(youtube,user_channel_id)
    channel_df=pd.DataFrame(channel_details,index=[0])
    user_playlist_id=channel_details["playlist_id"]
    user_video_ids= get_video_ids(youtube,user_playlist_id)
    video_details=get_video_data(youtube,user_video_ids)
    video_df=pd.DataFrame(video_details)
    video_df['published_date']=pd.to_datetime(video_df['published_date']).dt.date
    video_df['duration']=video_df['duration'].apply(lambda x:parse_duration(x))
    playlist_details=get_playlist_data(youtube,user_channel_id)
    playlist_df=pd.DataFrame(playlist_details)
    comment_details=get_comment_data(youtube,user_channel_id)
    comment_df=pd.DataFrame(comment_details)
    comment_df['comment_published_date']=pd.to_datetime(comment_df['comment_published_date']).dt.date
#Data Migrated To SQL:
#Connect to MySQL Server with Localhost:   
    myconnection=pymysql.connect(host='127.0.0.1',user='root',passwd='Geethu!20D')
    cur=myconnection.cursor() 

 #Create a DataBase or Used Existed One:
    cur.execute("create database if not exists youtube")
    myconnection=pymysql.connect(host='127.0.0.1',user='root',passwd='Geethu!20D',database='youtube')
    cur=myconnection.cursor()

#Create Table and Insert Data 
    cur.execute("create table if not exists channel(channel_id varchar(255)unique not null ,channel_name varchar(255),channel_description text,subscriber_count int,video_count int,view_count bigint,playlist_id varchar(255))")   
    try: 
     sql = "insert  into channel(channel_id,channel_name,channel_description,subscriber_count,video_count,view_count,playlist_id) values (%s,%s,%s,%s,%s,%s,%s)"
     for i in range(0,len(channel_df)):
          cur.execute(sql,tuple(channel_df.iloc[i]))
          myconnection.commit() 
     st.markdown(
        f"<h1 style='color:#539165; font-size: 24px;'>Data sucessfully Migrated to MySQL </h1>",
       unsafe_allow_html=True,)    
    
       
    except:
       st.markdown(
         f"<h1 style='color:#D83F31; font-size: 18px;'>Duplicate Entry,select another channel </h1>",
        unsafe_allow_html=True,)
        
    cur.execute("create table if not exists video(video_id varchar(255) unique not null ,channel_id varchar(255),video_name varchar(255),video_description text,published_date date,view_count bigint,like_count int,favourite_count int,comment_count int,duration varchar(255),caption_status varchar(255))")
    try:
       sql = "insert into video(video_id,channel_id,video_name,video_description,published_date,view_count,like_count,favourite_count,comment_count,duration,caption_status) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
       for i in range(0,len(video_df)):
             cur.execute(sql,tuple(video_df.iloc[i]))
             myconnection.commit()
    except:
     print("")  

    cur.execute("create table if not exists playlist(playlist_id varchar(255) unique not null,channel_id varchar(255),playlist_name varchar(255))")
    try:
       sql = "insert into playlist(playlist_id,channel_id,playlist_name) values (%s,%s,%s)"
       for i in range(0,len(playlist_details)):
            cur.execute(sql,tuple(playlist_df.iloc[i]))
            myconnection.commit() 
    except:     
     print("")                       
           
    cur.execute("create table if not exists comment(comment_id varchar(255) unique not null,video_id varchar(255),channel_id varchar(255) ,comment_text text,comment_author text,comment_published_date date)")
    try:
        sql = "insert into comment(comment_id,video_id,channel_id,comment_text,comment_author,comment_published_date) values (%s,%s,%s,%s,%s,%s)"
        for i in range(0,len(comment_details)):
            cur.execute(sql,tuple(comment_df.iloc[i]))
            myconnection.commit()
    except:   
     st.write("")
except:
    st.write("")    
     
 
#-------------------------------------------------------------------------------------------------------------------------------------------------------------     
#Select the Query and get the answer for it:  
st.markdown(
    f"<h1 style='color:#2F4858; font-size: 20px;'>DATA ANALYSIS</h1>",
    unsafe_allow_html=True,)

try:
 myconnection=pymysql.connect(host='127.0.0.1',user='root',passwd='Geethu!20D',database='youtube')
 cur=myconnection.cursor()
except:
    print("") 

query=st.selectbox(':grey[**Select your query:**]', ['SELECT',
'1. What are the names of all the videos and their corresponding channels?',
'2. Which channels have the most number of videos, and how many videos do they have?',
'3. What are the top 10 most viewed videos and their respective channels?',
'4. How many comments were made on each video, and what are their corresponding video names?',
'5. Which videos have the highest number of likes, and what are their corresponding channel names?',
'6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
'7. What is the total number of views for each channel, and what are their corresponding channel names?',
'8. What are the names of all the channels that have published videos in the year 2023?',
'9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
'10. Which videos have the highest number of comments, and what are their corresponding channel names?'],key='collection_question')

if query=='Select':   
   st.write(" ")

elif query=='1. What are the names of all the videos and their corresponding channels?':
    cur.execute("select c.channel_name,v.video_name from video as v join channel as c on c.channel_id=v.channel_id")
    result_1 = cur.fetchall()
    df1 = pd.DataFrame(result_1,columns=['Channel Name','Video Name']).reset_index(drop=True) 
    st.dataframe(df1)

elif query=='2. Which channels have the most number of videos, and how many videos do they have?':   
    cur.execute("select channel_name,video_count from channel order by video_count desc ")
    result_2 = cur.fetchall()
    df2 = pd.DataFrame(result_2,columns=['Channel Name','Video Count']).reset_index(drop=True)      
    st.dataframe(df2)

elif query=='3. What are the top 10 most viewed videos and their respective channels?':   
    cur.execute("select c.channel_name,v.video_name,v.view_count from channel as c join video as v on c.channel_id=v.channel_id order by view_count desc limit 10")
    result_3 = cur.fetchall()
    df3 = pd.DataFrame(result_3,columns=['Channel Name','Video Name','View Count']).reset_index(drop=True)      
    st.dataframe(df3)
     
elif query=='4. How many comments were made on each video, and what are their corresponding video names?':     
     cur.execute("select c.channel_name,v.video_name,count(ct.comment_id) as total_comment from video as v join channel as c on v.channel_id=c.channel_id join comment as ct on v.video_id=ct.video_id group by v.video_name,c.channel_name order by total_comment desc ") 
     result_4 = cur.fetchall()
     df4 = pd.DataFrame(result_4,columns=['Channel Name','Video Name','Total Comment']).reset_index(drop=True)
     st.dataframe(df4) 

elif query=='5. Which videos have the highest number of likes, and what are their corresponding channel names?':
      cur.execute("select distinct channel_name, first_value (video_name) over (partition by channel_name order by like_count desc) as fv,max(like_count) over (partition by channel_name) as like_count from channel join video on channel.channel_id=video.channel_id order by like_count desc")
      result_5= cur.fetchall()
      df5 = pd.DataFrame(result_5,columns=['Channel Name','Video Name','Like Count']).reset_index(drop=True)
      st.dataframe(df5)
    
elif query=='6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
     cur.execute("select c.channel_name,v.video_name,v.like_count from video as v join channel as c on c.channel_id=v.channel_id order by like_count desc")
     result_6= cur.fetchall()
     df6 = pd.DataFrame(result_6,columns=['Channel Name','Video Name','Like Count']).reset_index(drop=True)    
     st.dataframe(df6)

elif query=='7. What is the total number of views for each channel, and what are their corresponding channel names?':
     cur.execute("select channel_name,view_count from channel order by view_count desc")
     result_7= cur.fetchall()
     df7 = pd.DataFrame(result_7,columns=['Channel Name','View Count']).reset_index(drop=True)    
     st.dataframe(df7)
    
elif query=='8. What are the names of all the channels that have published videos in the year 2023?':
     cur.execute("select c.channel_name,v.video_name,v.published_date from channel as c join video as v on c.channel_id=v.channel_id where v.published_date like '2023%'")
     result_8= cur.fetchall()
     df8 = pd.DataFrame(result_8,columns=['Channel Name','Video Name','Published Date']).reset_index(drop=True)
     st.dataframe(df8)

elif query=='9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
     cur.execute("select c.channel_name, avg(v.duration) as average from channel as c join playlist as p on c.channel_id = p.channel_id join video as v on p.channel_id = v.channel_id group by c.channel_name order by avg(v.duration) desc")
     result_9= cur.fetchall()
     df9 = pd.DataFrame(result_9,columns=['Channel Name','Average']).reset_index(drop=True)
     st.dataframe(df9)
    
elif query=='10. Which videos have the highest number of comments, and what are their corresponding channel names?':
     cur.execute("select distinct channel_name, first_value(video_name) over (partition by channel_name order by comment_count desc) as cv,max(comment_count) over (partition by channel_name) as comment_count from channel join video on channel.channel_id=video.channel_id order by comment_count desc")
     result_10= cur.fetchall()
     df10 = pd.DataFrame(result_10,columns=['Channel Name','Video Name','Comment Count']).reset_index(drop=True)
     st.dataframe(df10)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------     





