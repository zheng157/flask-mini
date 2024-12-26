;
var account_set_ops = {
    init:function(){
        this.eventBind();
    },
    eventBind:function(){
        $(".wrap_account_set .save").click(function(){
            var btn_target = $(this);
            if( btn_target.hasClass("disabled") ){
                common_ops.alert("正在处理!!请不要重复提交~~");
                return;
            }
            // 姓名:
            var nickname_target = $(".wrap_account_set input[name=nickname]");
            var nickname = nickname_target.val();
            // 手机:
            var mobile_target = $(".wrap_account_set input[name=mobile]");
            var mobile = mobile_target.val();
            // 邮箱:
            var email_target = $(".wrap_account_set input[name=email]");
            var email = email_target.val();
            // 登录名:
            var login_name_target = $(".wrap_account_set input[name=login_name]");
            var login_name = login_name_target.val();
            // 登录密码:
            var login_pwd_target = $(".wrap_account_set input[name=login_pwd]");
            var login_pwd = login_pwd_target.val();




            if( !nickname || nickname.length < 2 ){
                common_ops.tip( "请输入符合规范的姓名~~",nickname_target );
                return false;
            };

            if( !mobile || mobile.length < 1 ){
                common_ops.tip( "请输入符合规范手机号码~~",mobile_target );
                return false;
            };

            if( !email || email.length < 2 ){
                common_ops.tip( "请输入符合规范的邮箱~~",email_target );
                return false;
            };


            if( !login_name || login_name.length < 2 ){
                common_ops.tip( "请输入符合规范的用户名",login_name_target );
                return false;
            };

            if( !login_pwd || login_pwd.length < 6 ){
                common_ops.tip( "请输入符合规范的密码",login_pwd_target );
                return false;
            };

            // 如果后端没反映，就返回btn_target
            btn_target.addClass("disabled");

            var data = {
                nickname: nickname,
                mobile: mobile,
                email: email,
                login_name:login_name,
                login_pwd:login_pwd,
                id:$(".wrap_account_set input[name=id]").val()
            };

            $.ajax({
                url:common_ops.buildUrl( "/account/set" ),
                type:'POST',
                data:data,
                dataType:'json',
                success:function( res ){
                    btn_target.removeClass("disabled");
                    var callback = null;
                    if( res.code == 200 ){
                        callback = function(){
                            window.location.href = common_ops.buildUrl("/account/index");
                        }
                    }
                    common_ops.alert( res.msg,callback );
                }
            });

        });
    }
};

$(document).ready( function(){
    account_set_ops.init();
} );