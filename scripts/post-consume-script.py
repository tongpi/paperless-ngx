#!/usr/bin/env python3

import os
import json
import re

# TODO: The user can use anything in the standard library, installed for paperless
# or use the custom startup scripts to install additional libraries via pip
import requests

def _set_auth_tokens(paperless_url: str, timeout: float, session: requests.Session):
    # TODO: You fill these in or otherwise provide them
    credentials = {"username": "userXXX", "password": "pwdXXX"}

    response = session.get(paperless_url, timeout=timeout)
    response.raise_for_status()

    csrf_token = response.cookies["csrftoken"]

    response = session.post(
        paperless_url + "/api/token/",
        data=json.dumps(credentials),
        # headers={"X-CSRFToken": csrf_token},
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )

    response.raise_for_status()

    api_token = response.json()["token"]
    
    session.headers.update(
        {"Authorization": f"Token {api_token}", f"X-CSRFToken": csrf_token}
    )

if __name__ == "__main__":
    print("执行后处理脚本,保存文档到向量数据库中，以便支持文档的语义检索......")
    # Running inside the Docker container
    # TODO: Update this as needed
    paperless_url = "http://192.168.15.130:5088"
    nice3_url = "http://192.168.15.130:5006"
    timeout = 5.0

    with requests.Session() as sess:
        # Set tokens for the appropriate header auth
        _set_auth_tokens(paperless_url, timeout, sess)

        # Get the PK as provided via post-consume
        doc_pk = int(os.environ["DOCUMENT_ID"])

        # Query the API for the document info
        doc_info_resp = sess.get(
            paperless_url + f"/api/documents/{doc_pk}/", timeout=timeout
        )
        doc_info_resp.raise_for_status()
        doc_info = doc_info_resp.json()
        
        data = {key: doc_info[key] for key in ['id', 'title', 'content','original_file_name','archived_file_name','created_date']}
        if doc_info['archived_file_name'] is None:
           doc_info['archived_file_name'] =  f'{doc_info["title"]}.pdf'
        
        
        with requests.Session() as nice3_session:
                response = nice3_session.post(
                    nice3_url + "/createDocument/",
                    data=json.dumps({key: doc_info[key] for key in ['id', 'title', 'content','original_file_name','archived_file_name','created_date']}),
                    headers={"Content-Type": "application/json"},
                    timeout=timeout,
                )
                print(f'{response.json()} 个文档保存到向量数据库中,文档标题：{doc_info["title"]}')
                response.raise_for_status()            
        # {'id': 473, 'correspondent': None, 'document_type': None, 'storage_path': None, 'title': '监管严阵以待 套购寸步难行 ——海南强化离岛免税走私风险监管', 'content': 'ddddd', 
        # 'tags': [], 'created': '2024-01-29T16:35:35+08:00', 
        # 'created_date': '2024-01-29', 'modified': '2024-01-29T16:35:40.995301+08:00', 
        # 'added': '2024-01-29T16:35:40.488914+08:00', 
        # 'archive_serial_number': None, 
        # 'original_file_name': '监管严阵以待 套购寸步难行 ——海南强化离岛免税走私风险监管.pdf', 
        # 'archived_file_name': '2024-01-29 监管严阵以待 套购寸步难行 ——海南强化离岛免税走私风险监管.pdf', 
        # 'owner': 3, 
        # 'user_can_change': True, 
        # 'is_shared_by_requester': False, 
        # 'notes': [], 'custom_fields': []}        
   
        
        # # Extract the currently assigned values
        # correspondent = doc_info["correspondent"]
        # doc_type = doc_info["document_type"]
        # doc_original_name = doc_info["original_file_name"]
        # # etc...

        # # Parse, set, otherwise choose new values
        # # TODO: Up to the user to decide how these new values should be set
        # # Use regex, etc to get the primary key of the new values
        # new_correspondent = 1
        # new_doc_type = 1

        # # Update the document
        # resp = sess.patch(
        #     paperless_url + f"/api/documents/{doc_pk}/",
        #     data=json.dumps({"correspondent": new_correspondent, "document_type": new_doc_type}),
        #     timeout=timeout,
        # )
        # resp.raise_for_status()