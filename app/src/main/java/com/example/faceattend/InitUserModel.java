package com.example.faceattend;

import org.json.JSONObject;

public class InitUserModel {
    JSONObject priv=new JSONObject();
    String token;
    String result;
    public  InitUserModel(JSONObject priv,String token){
        this.priv=priv;
        this.token=token;
    }

    public String getToken() {
        return token;
    }
    public String getResult(){
        return result;
    }
}
