// AI Token 代理服务系统
// Copyright (C) 2026
// License: GNU General Public License v3.0
// https://www.gnu.org/licenses/

const app = getApp();

Page({
  data: {
    flow: 0,
    tokenKey: "",
    modelList: [],
    selectedModel: "",
    selectedModelName: "请选择模型",
    selectedModelRatio: 1.0,
    modelUsage: {},
    usageList: []
  },

  onShow() {
    this.checkBalance();
    this.loadTokenKey();
    this.loadModels();
    this.loadModelUsage();
  },

  checkBalance() {
    const openid = wx.getStorageSync('openid');
    if (!openid) {
      wx.showToast({ title: '请先授权', icon: 'none' });
      return;
    }
    wx.request({
      url: `${app.globalData.apiBase}/api/balance`,
      data: { openid },
      success: res => {
        if (res.data.code === 200) {
          this.setData({ flow: res.data.flow, tokenKey: res.data.token_key || "" });
        }
      }
    });
  },

  loadTokenKey() {
    const openid = wx.getStorageSync('openid');
    if (!openid) return;
    wx.request({
      url: `${app.globalData.apiBase}/api/token-key`,
      data: { openid },
      success: res => {
        if (res.data.code === 200 && res.data.token_key) {
          this.setData({ tokenKey: res.data.token_key });
        }
      }
    });
  },

  copyToken() {
    if (this.data.tokenKey) {
      wx.setClipboardData({
        data: this.data.tokenKey,
        success: () => {
          wx.showToast({ title: '已复制到剪贴板', icon: 'success' });
        }
      });
    }
  },

  loadModels() {
    wx.request({
      url: `${app.globalData.apiBase}/api/models`,
      success: res => {
        if (res.data.code === 200 && res.data.models) {
          const modelList = res.data.models;
          const savedModel = wx.getStorageSync('selectedModel') || modelList[0]?.id || "";
          const selected = modelList.find(m => m.id === savedModel) || modelList[0] || {};
          this.setData({
            modelList: modelList,
            selectedModel: selected.id || "",
            selectedModelName: selected.name || "请选择模型",
            selectedModelRatio: selected.ratio || 1.0
          });
        }
      }
    });
  },

  onModelChange(e) {
    const index = e.detail.value;
    const model = this.data.modelList[index];
    if (model) {
      wx.setStorageSync('selectedModel', model.id);
      this.setData({
        selectedModel: model.id,
        selectedModelName: model.name,
        selectedModelRatio: model.ratio || 1.0
      });
      wx.showToast({ title: `已切换到${model.name}`, icon: 'none' });
    }
  },

  loadModelUsage() {
    const openid = wx.getStorageSync('openid');
    if (!openid) return;
    wx.request({
      url: `${app.globalData.apiBase}/api/model-usage`,
      data: { openid },
      success: res => {
        if (res.data.code === 200 && res.data.model_usage) {
          const modelUsage = res.data.model_usage;
          const usageList = Object.entries(modelUsage).map(([model, count]) => {
            const modelInfo = this.data.modelList.find(m => m.id === model) || {};
            return {
              model: model,
              name: modelInfo.name || model,
              count: count
            };
          });
          this.setData({ modelUsage, usageList });
        }
      }
    });
  }
});