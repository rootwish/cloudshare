'use strict';
import React, { Component, PropTypes } from 'react';

import LayoutHeader from './LayoutHeader';
import LayoutContainer from './LayoutContainer';

class Layout extends Component {
  render() {
    return (
      <div className="cs-layout">
        <LayoutHeader />
        <LayoutContainer>
          {this.props.children}
        </LayoutContainer>
      </div>
      
    );
  }
}

Layout.propTypes = {
  children: PropTypes.oneOfType([PropTypes.element, PropTypes.arrayOf(PropTypes.element)])
};

export default Layout;
