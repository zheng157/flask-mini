//获取应用实例
var app = getApp();
Page({
    data: {},
    onLoad() {

    },
    onShow() {
        let that = this;
        that.setData({
            user_info: {
                nickname: "测试号",
                avatar_url: "/images/more/logo.png"
            },
		})
		that.getInfo()
	},
	getInfo:function (){
        var that = this;
        wx.request({
            url: app.buildUrl("/member/info"),
            header: app.getRequestHeader(),
            success: function (res) {
                var resp = res.data;
                if (resp.code != 200) {
                    app.alert({"content": resp.msg});
                    return;
                }
                that.setData({
                   user_info:resp.data.user_info
                });

            }
        });
    }
});