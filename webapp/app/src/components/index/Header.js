'use strict';
import React, { Component } from 'react';

import Feature from './Feature';

import './header.less';

import LogoImg from '../../image/logo.png';

export default class Header extends Component {

  render() {
    return (
      <div className="cs-layout-top">
        <div className="cs-layout-herader">
          <div className="cs-layout-wrapper">
            <div className="cs-layout-logo">
              <img src={LogoImg} alt="Logo" />
            </div>
            <div className="cs-layout-feature">
              <Feature />
            </div>
          </div>
        </div>
      </div>
    );
  }
}