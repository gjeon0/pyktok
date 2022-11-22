# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 14:06:01 2022

@author: freelon
"""

import browser_cookie3
from bs4 import BeautifulSoup
from datetime import datetime
import json
import numpy as np
import os
import pandas as pd
import random
import re
import requests
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeiumService #sic
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from webdriver_manager.firefox import GeckoDriverManager

headers = {'Accept-Encoding': 'gzip, deflate, sdch',
           'Accept-Language': 'en-US,en;q=0.8',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Cache-Control': 'max-age=0',
           'Connection': 'keep-alive'}
cookies = browser_cookie3.load()

def get_account_video_urls(user_url,browser_name=None):
    tt_json = get_tiktok_json(user_url,browser_name)
    video_ids = tt_json['ItemList']['user-post']['list']
    tt_account = tt_json['UserPage']['uniqueId']
    url_seg_1 = 'https://www.tiktok.com/@'
    url_seg_2 = '/video/'
    video_urls = [url_seg_1 + tt_account + url_seg_2 + u for u in video_ids]
    return video_urls

def get_tiktok_json(video_url,browser_name=None):
    global cookies
    if browser_name is not None:
        cookies = getattr(browser_cookie3,browser_name)(domain_name='tiktok.com')
    tt = requests.get(video_url,
                      headers=headers,
                      cookies=cookies,
                      timeout=20)
    soup = BeautifulSoup(tt.text, "html.parser")
    tt_script = soup.find('script', attrs={'id':"SIGI_STATE"})
    try:
        tt_json = json.loads(tt_script.string)
    except AttributeError:
        print("The function encountered a downstream error and did not deliver any data, which happens periodically (not sure why). Please try again later.")
        return
    return tt_json

def generate_data_row(video_obj):
    data_header = ['video_id',
                   'video_timestamp',
                   'video_duration',
                   'video_locationcreated',
                   'video_diggcount',
                   'video_sharecount',
                   'video_commentcount',
                   'video_playcount',
                   'video_description',
                   'video_is_ad',
                   'video_stickers',
                   'author_username',
                   'author_name',
                   'author_followercount',
                   'author_followingcount',
                   'author_heartcount',
                   'author_videocount',
                   'author_diggcount',
                   'author_verified']
    data_list = []
    data_list.append(video_obj['id'])
    try:
        ctime = video_obj['createTime']
        data_list.append(datetime.fromtimestamp(int(ctime)).isoformat())
    except Exception:
        data_list.append('')
    try:
        data_list.append(video_obj['video']['duration'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['locationCreated'])
    except Exception:
        data_list.append('')
    try:
        data_list.append(video_obj['stats']['diggCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['stats']['shareCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['stats']['commentCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['stats']['playCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['desc'])
    except Exception:
        data_list.append('')
    try:
        data_list.append(video_obj['isAd'])
    except Exception:
        data_list.append(False)
    try:
        video_stickers = []
        for sticker in video_obj['stickersOnItem']:
            for text in sticker['stickerText']:
                video_stickers.append(text)
        data_list.append(';'.join(video_stickers))
    except Exception:
        data_list.append('')
    try:
        data_list.append(video_obj['author']['uniqueId'])
    except Exception:
        try:
            data_list.append(video_obj['author'])
        except Exception:
            data_list.append('')
    try:
        data_list.append(video_obj['author']['nickname'])
    except Exception:
        try:
            data_list.append(video_obj['nickname'])
        except Exception:
            data_list.append('')
    try:
        data_list.append(video_obj['authorStats']['followerCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['authorStats']['followingCount'])
    except Exception:
        data_list.append(np.nan)   
    try:
        data_list.append(video_obj['authorStats']['heartCount'])
    except Exception:
        data_list.append(np.nan)   
    try:
        data_list.append(video_obj['authorStats']['videoCount'])
    except Exception:
        data_list.append(np.nan)    
    try:
        data_list.append(video_obj['authorStats']['diggCount'])
    except Exception:
        data_list.append(np.nan)
    try:
        data_list.append(video_obj['author']['verified'])
    except Exception:
        data_list.append(False)
    data_row = pd.DataFrame(dict(zip(data_header,data_list)),index=[0])
    return data_row

def save_tiktok(video_url,
                save_video=True,
                metadata_fn='',
                browser_name=None):
    if save_video == False and metadata_fn == '':
        print('Since save_video and metadata_fn are both False/blank, the program did nothing.')
        return

    tt_json = get_tiktok_json(video_url,browser_name)

    if save_video == True:
        tt_video_url = tt_json['ItemList']['video']['preloadList'][0]['url']
        regex_url = re.findall('(?<=@)(.+?)(?=\?|$)',video_url)[0]
        video_fn = regex_url.replace('/','_') + '.mp4'
        with open(video_fn, 'wb') as fn:
            fn.write(tt_video_url.content)
        print("Saved video\n",tt_video_url,"\nto\n",os.getcwd())
    
    if metadata_fn != '':
        data_slot = tt_json['ItemModule'][list(tt_json['ItemModule'].keys())[0]]
        data_row = generate_data_row(data_slot)
        try:
            data_row.loc[0,"author_verified"] = tt_json['UserModule']['users'][list(tt_json['UserModule']['users'].keys())[0]]['verified']
        except Exception:
            pass
        if os.path.exists(metadata_fn):
            metadata = pd.read_csv(metadata_fn,keep_default_na=False)
            combined_data = pd.concat([metadata,data_row])
        else:
            combined_data = data_row
        combined_data.to_csv(metadata_fn,index=False)
        print("Saved metadata for video\n",video_url,"\nto\n",os.getcwd())

def save_tiktok_multi(video_urls,
                      save_video=True,
                      metadata_fn='',
                      sleep=4,
                      browser_name=None):
    if type(video_urls) is str:
        tt_urls = open(video_urls).read().splitlines()
    else:
        tt_urls = video_urls
    for u in tt_urls:
        save_tiktok(u,save_video,metadata_fn,browser_name)
        time.sleep(random.randint(1, sleep))
    print('Saved',len(tt_urls),'video files and/or lines of metadata')

def save_tiktok_by_keyword(keyword,
                           save_videos=False,
                           save_metadata=True,
                           max_urls=np.inf,
                           cursor=0,
                           sleep=4,
                           browser_name=None):
    global cookies
    if browser_name is not None:
        cookies = getattr(browser_cookie3,browser_name)(domain_name='tiktok.com')
    metadata_fn = keyword + '_tiktok_metadata.csv' #only used if save_metadata == True
    while cursor < max_urls:
        params = {'device_id':'1234567890123456789',
                  'keyword':keyword,
                  'offset':cursor,
                  'count':'20'} #doesn't change anything--why?
        try:
            response = requests.get('https://www.tiktok.com/api/search/item/full/',
                                    params=params,
                                    cookies=cookies)
            data = response.json()
            videos = data['item_list']
            video_df = pd.DataFrame()
            
            for v in videos:
                if save_videos == True:
                    video_url = 'https://tiktok.com/@' + v['author']['uniqueId'] + '/video/' + v['id']
                    save_tiktok(video_url,True,browser_name=browser_name)
                if save_metadata == True:
                    data_row = generate_data_row(v)
                    video_df = pd.concat([video_df,data_row])
            if save_metadata == True:
                if os.path.exists(metadata_fn):
                    metadata = pd.read_csv(metadata_fn,keep_default_na=False)
                    combined_data = pd.concat([metadata,video_df])
                    combined_data['video_id'] = combined_data.video_id.astype(str)
                else:
                    combined_data = video_df
                combined_data.drop_duplicates('video_id').to_csv(metadata_fn,index=False)
            cursor = cursor + len(videos)
            print('Saved',cursor,'total videos and/or metadata rows.')
            if data["has_more"] != 1:
                break
            time.sleep(random.randint(1,sleep))   
        except Exception as e:
            print(type(e).__name__ +': '+str(e),'\nStopped at cursor=',cursor)
            return
    print('Done.')
    
def save_visible_comments(video_url,
                          comment_fn=None,
                          browser='chromium'):
    start_time = time.time()
    c_options = ChromeOptions()
    c_options.add_argument("--headless")
    f_options = FirefoxOptions()
    f_options.add_argument("--headless")
    if browser == 'chromium':
        driver = webdriver.Chrome(service=ChromeiumService(
                                      ChromeDriverManager(
                                          chrome_type=ChromeType.CHROMIUM).install()),
                                  options=c_options)
    elif browser == 'chrome':
        driver = webdriver.Chrome(service=ChromeiumService(ChromeDriverManager().install()),options=c_options)
    elif browser == 'firefox':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()),options=f_options)
    driver.get(video_url)
    wait = WebDriverWait(driver,10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                                               'span.tiktok-ku14zo-SpanUserNameText.e1g2efjf3')))
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    ids_tags = soup.find_all('div',{'class':re.compile('DivCommentContentContainer')})
    comment_ids = [i.get('id') for i in ids_tags]
    names_tags = soup.find_all('a',attrs={'class':re.compile("StyledUserLinkName")})
    styled_names = [i.text.strip() for i in names_tags]
    screen_names = [i.get('href').replace('/','') for i in names_tags]
    comments_tags = soup.find_all('p',attrs={'class':re.compile("PCommentText")})
    comments = [i.text.strip() for i in comments_tags]
    likes_tags = soup.find_all('span',attrs={'class':re.compile('SpanCount')})
    likes = [int(i.text.strip()) 
             if i.text.strip().isnumeric() 
             else i.text.strip() 
             for i 
             in likes_tags]
    timestamp = datetime.now().isoformat()
    data_header = ['comment_id','styled_name','screen_name','comment','like_count','time_collected']
    data_list = [comment_ids,styled_names,screen_names,comments,likes,[timestamp] * len(likes)]
    data_frame = pd.DataFrame(data_list,index=data_header).T
    
    if comment_fn is None:
        regex_url = re.findall('(?<=@)(.+?)(?=\?|$)',video_url)[0]
        comment_fn = regex_url.replace('/','_') + '_tiktok_comments.csv'
    if os.path.exists(comment_fn):
        existing_data = pd.read_csv(comment_fn,keep_default_na=False)
        combined_data = pd.concat([existing_data,data_frame])
        combined_data['comment_id'] = combined_data.comment_id.astype(str)
        combined_data.drop_duplicates('comment_id').to_csv(comment_fn,index=False)
    else:
        data_frame.to_csv(comment_fn,index=False)
    print('Comments saved to file',comment_fn,'in',round(time.time() - start_time,2),'secs.')
