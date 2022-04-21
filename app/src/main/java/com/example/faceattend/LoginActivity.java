package com.example.faceattend;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.toolbox.JsonObjectRequest;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GetTokenResult;
import com.google.gson.Gson;

import org.json.JSONException;
import org.json.JSONObject;

import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;


public class LoginActivity extends AppCompatActivity {
    private FirebaseAuth mAuth;
    FirebaseUser mUser;
    private static final String TAG="EmailPassword";
    EditText email,password;
    TextView loginButton,regButton;
    //String idToken="";
    FirebaseAuth.AuthStateListener mAuthListener;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mUser = FirebaseAuth.getInstance().getCurrentUser();
        //Intent in=new Intent(this,MainActivity.class);
        if (mUser!= null) {
            mUser.getIdToken(true)
                    .addOnCompleteListener(new OnCompleteListener<GetTokenResult>() {
                        public void onComplete(@NonNull Task<GetTokenResult> task) {
                            if (task.isSuccessful()) {
                                int i=0;
                                JSONObject jsonParam = new JSONObject();
                                try {
                                    jsonParam.put("priv",i);
                                } catch (JSONException e) {
                                    e.printStackTrace();
                                }

                                String idToken = task.getResult().getToken();
                                //in.putExtra("token",idToken);
                                //startActivity(in);
                                String prepare="Bearer "+idToken;
                                Log.d("TOKEN",idToken);
                                Log.d("json", String.valueOf(jsonParam));
                                GETApi service =
                                        ServiceGenerator.createService(GETApi.class);
                                JsonObj j=new JsonObj();
                                Call<InitUserModel> call =service.verifyToken("Bearer "+idToken,j);
                                //Log.d("err", );
                                call.enqueue(new Callback<InitUserModel>() {
                                    @Override
                                    public void onResponse(Call<InitUserModel> call,
                                                           retrofit2.Response<InitUserModel> response) {
                                        Log.v("Response", String.valueOf(response));
                                        InitUserModel res=response.body();

                                        try {
                                            JSONObject jsonObject = new JSONObject(new Gson().toJson(response));
                                            JSONObject body=jsonObject.getJSONObject("body");
                                            Log.v("fea",body.getString("result"));
                                        } catch (JSONException e) {
                                            e.printStackTrace();
                                        }
                                        //Toast.makeText(LoginActivity.this, response.toString(), Toast.LENGTH_SHORT).show();

//                try {
//                    //JSONObject jsonObject = new JSONObject(response.toString());
//                    Toast.makeText(MainActivity.this, response.toString(), Toast.LENGTH_SHORT).show();
//                } catch (JSONException e) {
//                    e.printStackTrace();
//                }


                                    }

                                    @Override
                                    public void onFailure(Call<InitUserModel> call, Throwable t) {
                                        Log.e("Upload error:", t.getMessage());
                                    }
                                });


                                        // Send token to your backend via HTTPS
                                // ...
                            } else {
                                // Handle error -> task.getException();
                            }
                        }
                    });



            startActivity(new Intent(this, DashboardActivity.class));
            finish();
        }
        setContentView(R.layout.activity_login);
        mAuth=FirebaseAuth.getInstance();
        loginButton = findViewById(R.id.loginButton);
        regButton=findViewById(R.id.regButton);
        email= findViewById(R.id.emailInput);
        password=findViewById(R.id.passwordInput);
        loginButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                signIn();
            }
        });
        regButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(LoginActivity.this,RegisterActivity.class));
            }
        });


    }
    public void signIn()
    {
        Log.d(TAG,"signIn"+email);
        String em=email.getText().toString();
        String pass=password.getText().toString();
        mAuth.signInWithEmailAndPassword(em,pass)
                .addOnCompleteListener(LoginActivity.this, new OnCompleteListener<AuthResult>() {
                    @Override
                    public void onComplete(@NonNull Task<AuthResult> task) {
                        if(task.isSuccessful()){

                            Toast.makeText(LoginActivity.this,"Login Successful",Toast.LENGTH_SHORT).show();
                            startActivity(new Intent(LoginActivity.this,MainActivity.class));
                        }else{
                            Log.w(TAG,"signInWithEmail:failure",task.getException());
                            Toast.makeText(LoginActivity.this,"Login Failed",Toast.LENGTH_SHORT).show();
                        }
                    }
                });
    }
}