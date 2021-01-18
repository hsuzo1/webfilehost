/*!
  * 2021-01-18
  * Copyright 2011-2020 zhang xuzhou
  */
//<!--更新用户名-->
    function getuser(){
        $('#usernames').text("");
//<!--        $('#usernames').append('<option value=""></option>');-->
        var dept = $("#dept").val()
        $.ajax({
            url:"/getuser/" + dept,
            type:"post",
            success:function(data){
                for (var x in data) {
                    $('#usernames').append('<option value=' + x + '>' + data[x] +'</option>');
                    };
            },
        });
    }