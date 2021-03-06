'use strict';
import React, { Component, PropTypes } from 'react';
import { browserHistory } from 'react-router';

import { message } from 'antd';

import { API } from 'API';
import { confirmExcelUpload } from 'request/company';

import StorageUtil from 'utils/storage';

import websiteText from 'config/website-text';

const language = websiteText.zhCN;

const parseResponse = (data, info) => {
  let idObject = {},
      result = [];

  for (let i = 0, len = data.length; i < len; i++) {
    let item = data[i],
        id = item[1];

    if (item[0] === 'projectadd' || item[0] === 'companyadd') {
      if (!idObject.hasOwnProperty(id)) {
        idObject[id] = result.length;
        result.push(Object.assign({}, info[id], {
          type: item[0]
        }));
      }
    } else {
      if (idObject.hasOwnProperty(id)) {
        if (typeof result[idObject[id]].diff === 'undefined') {
          result[idObject[id]].diff = [];
        }
        result[idObject[id]].diff.push({
          dataIndex: item[2][1],
          value: item[2][2]
        });
      } else {
        idObject[id] = result.length;
        result.push(Object.assign({}, info[id], { 
          diff: [{
            dataIndex: item[2][1],
            value: item[2][2]
          }],
          type: null
        }));
      }
    }
  }

  return result;
};

class Company extends Component {
  constructor() {
    super();
    this.state = {
      fileList: [],
      previewList: [],
      dataSource: [],
      loading: false,
      uploading: false,
      disabled: true,
      status: 'ready'
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleConfirmUpload = this.handleConfirmUpload.bind(this);
  }

  handleChange(info) {
    const file = info.file;
    
    if (file.status === 'uploading') {
      this.setState({
        uploading: true
      });
    }

    if (file.status === 'error' || file.status === 'removed') {
      this.setState({
        uploading: false
      });
    }

    if (file.status === 'done' && file.response) {
      if (file.response.code === 200) {
        const dataSource = parseResponse(file.response.data, file.response.info);
        message.success(`上传${file.name}文件成功!`);
        this.setState({
          previewList: file.response.data,
          dataSource: dataSource,
          uploading: false,
          disabled: false
        });
      }
    }
  }

  handleConfirmUpload() {
    this.setState({
      loading: true,
      status: 'doing'
    });

    confirmExcelUpload({
      data: this.state.previewList
    }, json => {
      if (json.code === 200) {
        message.success(language.UPLOAD_SUCCESS_MSG);
        this.setState({
          loading: false,
          status: 'done'
        });
        
        setTimeout(() => {
          browserHistory.push('/pm/company/list');
        }, 1000);
      }
    });
  }

  render() {
    const uploadProps = {
      name: 'files',
      action: API.UPLOAD_EXCEL_API,
      header: {
        'Authorization': `Basic ${StorageUtil.get('token')}`,
        'Content-Type': 'application/json'
      },
      data: {
        project: StorageUtil.get('_pj')
      },
      onChange: this.handleChange
    };

    return (
      <div className="cs-company">
        {this.props.children &&
          React.cloneElement(this.props.children, {
            uploadProps: uploadProps,
            loading: this.state.loading,
            uploading: this.state.uploading,
            disabled: this.state.disabled,
            status: this.state.status,
            dataSource: this.state.dataSource,
            onConfirmUpload: this.handleConfirmUpload
          })}
      </div>
    );
  }
}

Company.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.element,
    PropTypes.arrayOf(PropTypes.element)
  ]),
  history: PropTypes.object
};

export default Company;
