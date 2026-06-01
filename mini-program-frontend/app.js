// AI Token 代理服务系统
// Copyright (C) 2026
// License: GNU General Public License v3.0
// https://www.gnu.org/licenses/

App({
  globalData: {
    apiBase: 'https://你的域名',
    templateId: '你的订阅消息模板ID'
  },

  onLaunch() {
    this.getOpenid();
  },

  getOpenid() {
    const that = this;
    wx.login({
      success: res => {
        if (res.code) {
          wx.request({
            url: `${that.globalData.apiBase}/api/get-openid`,
            data: { code: res.code },
            success(r) {
              wx.setStorageSync('openid', r.data.openid);
            }
          });
        }
      }
    });
  }
})