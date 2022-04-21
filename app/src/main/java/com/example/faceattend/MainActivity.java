package com.example.faceattend;

import com.android.volley.AuthFailureError;
import com.android.volley.DefaultRetryPolicy;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.RetryPolicy;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.net.Uri;
import android.os.Bundle;
//import android.os.FileUtils;
import android.provider.MediaStore;
import android.text.Html;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.webkit.MimeTypeMap;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.ActionBar;
import androidx.appcompat.app.AppCompatActivity;
import androidx.loader.content.CursorLoader;

import com.androidnetworking.AndroidNetworking;
import com.androidnetworking.error.ANError;
import com.androidnetworking.interfaces.JSONArrayRequestListener;
import com.example.faceattend.UploadApis;

import org.apache.commons.io.FileUtils;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.w3c.dom.Text;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class MainActivity extends AppCompatActivity {
    String token;
    EditText t;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Intent i=getIntent();
        token=i.getStringExtra("token");
        t=findViewById(R.id.tokenValue);
        t.setText(token);
//        ActionBar actionBar;
//        actionBar = getSupportActionBar();
//
//        // Define ColorDrawable object and parse color
//        // using parseColor method
//        // with color hash code as its parameter
//        ColorDrawable colorDrawable
//                = new ColorDrawable(Color.parseColor("#FFFFFF"));
//
//        // Set BackgroundDrawable
//        actionBar.setBackgroundDrawable(colorDrawable);
//        actionBar.setTitle("Dashboard");
//        actionBar.setTitle(Html.fromHtml("<font color=\"black\">" + getString(R.string.app_name) + "</font>"));

        Button upload=findViewById(R.id.BSelectImage);
        upload.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showFileChooser();
//                Retrofit retrofit = new Retrofit.Builder().baseUrl("https://attent777.herokuapp.com/")
//                        .addConverterFactory(GsonConverterFactory.create())
//                        .build();
//
//                GETApi GETApi = retrofit.create(GETApi.class);
//
//                Call <DataModel> listCall = GETApi.getHello();
//                listCall.enqueue(new Callback <DataModel>() {
//                    @Override
//                    public void onResponse(Call<DataModel> call, retrofit2.Response<DataModel> response) {
//
//                            System.out.println("hi");
//                            Toast.makeText(MainActivity.this,response.body().getHello(), Toast.LENGTH_LONG).show();
//                            return;
//                    }
//
//                    @Override
//                    public void onFailure(Call<DataModel> call, Throwable t) {
//                        Log.e("Success","done");
//                        Toast.makeText(MainActivity.this,"Nope",Toast.LENGTH_LONG).show();
//                        t.printStackTrace();
//                    }
//                });
//
//
//



                    }
               // showFileChooser();
//                AndroidNetworking.get("https://attent777.herokuapp.com/hello")
//                        .build()
//                        .getAsJSONArray(new JSONArrayRequestListener() {
//                            @Override
//                            public void onResponse(JSONArray response) {
//                                Toast.makeText(getApplicationContext(),"Done",Toast.LENGTH_LONG).show();
//                                System.out.println(response);
//                                // do anything with response
//                            }
//                            @Override
//                            public void onError(ANError error) {
//                                // handle error
//                            }
                        //});
                //Toast.makeText(getApplicationContext(),"Done",Toast.LENGTH_LONG).show();
                //uploadImage();
                //getData();
            });
        //});

    }
    private void showFileChooser() {
        Intent pickImageIntent = new Intent(Intent.ACTION_PICK,
                android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        pickImageIntent.setType("image/*");
        pickImageIntent.putExtra("aspectX", 1);
        pickImageIntent.putExtra("aspectY", 1);
        pickImageIntent.putExtra("scale", true);
        pickImageIntent.putExtra("outputFormat",
                Bitmap.CompressFormat.JPEG);
        startActivityForResult(pickImageIntent, 1);
    }
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode == RESULT_OK && data != null && data.getData() != null) {
            Uri filePath = data.getData();
            try {
                Bitmap bitmap = MediaStore.Images.Media.getBitmap(getContentResolver(), filePath);
                Bitmap lastBitmap = null;
                lastBitmap = bitmap;
                //encoding image to string
                //String image = getStringImage(lastBitmap);
                //Log.d("image",);
                //passing the image to volley
                uploadFile(lastBitmap,filePath);

            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
    private String getRealPathFromURI(Uri contentUri) {
        String[] proj = {MediaStore.Images.Media.DATA};
        CursorLoader loader = new CursorLoader(this, contentUri, proj, null, null, null);
        Cursor cursor = loader.loadInBackground();
        int column_index = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.DATA);
        cursor.moveToFirst();
        String result = cursor.getString(column_index);
        cursor.close();
        return result;
    }
    private void uploadFile(Bitmap file,Uri fileUri) {
        // create upload service client
        GETApi service =
                ServiceGenerator.createService(GETApi.class);

        // https://github.com/iPaulPro/aFileChooser/blob/master/aFileChooser/src/com/ipaulpro/afilechooser/utils/FileUtils.java
        // use the FileUtils to get the actual file by uri
        //File file = File(RealPathUtils.getRealPathFromURI_API19(MainActivity.this, fileUri))
        File file1 = new File(getRealPathFromURI(fileUri));
        //File file1 = FileUtils;
        //showFileChooser();
        // create RequestBody instance from file
        RequestBody requestFile =
                RequestBody.create(MediaType.parse("multipart/form-data"), file1);

        // MultipartBody.Part is used to send also the actual file name
        MultipartBody.Part body =
                MultipartBody.Part.createFormData("picture", "jb", requestFile);

        // add another part within the multipart request
        //String descriptionString = "hello, this is description speaking";
        //RequestBody description =
                //RequestBody.create(
                        //okhttp3.MultipartBody.FORM, descriptionString);
        Call<ResponseBody> call = service.saveFace("tom","tom1", body);
        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call,
                                   retrofit2.Response<ResponseBody> response) {
                Log.v("Upload", String.valueOf(response.body()));
                Toast.makeText(MainActivity.this, response.toString(), Toast.LENGTH_SHORT).show();

//                try {
//                    //JSONObject jsonObject = new JSONObject(response.toString());
//                    Toast.makeText(MainActivity.this, response.toString(), Toast.LENGTH_SHORT).show();
//                } catch (JSONException e) {
//                    e.printStackTrace();
//                }


            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Log.e("Upload error:", t.getMessage());
            }
        });
    }
}

//    public String getStringImage(Bitmap bmp) {
//        ByteArrayOutputStream baos = new ByteArrayOutputStream();
//        bmp.compress(Bitmap.CompressFormat.JPEG, 100, baos);
//        byte[] imageBytes = baos.toByteArray();
//        String encodedImage = Base64.encodeToString(imageBytes, Base64.DEFAULT);
//        return encodedImage;
//
//    }
//    private void SendImage( final String image) {
//        String url="https://attent777.herokuapp.com/saveface?name=jb&uniqueId=jb24";
//        final StringRequest stringRequest = new StringRequest(Request.Method.POST, url,
//                new Response.Listener<String>() {
//                    @Override
//                    public void onResponse(String response) {
//                        Log.d("uploade", response);
//                        try {
//                            JSONObject jsonObject = new JSONObject(response);
//
//                        } catch (JSONException e) {
//                            e.printStackTrace();
//                        }
//                    }
//
//                },
//
//            new Response.ErrorListener() {
//        @Override
//        public void onErrorResponse(VolleyError error) {
//            Toast.makeText(MainActivity.this, "No internet connection", Toast.LENGTH_LONG).show();
//
//        }
//    }) {
//        @Override
//        protected Map<String, String> getParams() throws AuthFailureError {
//
//            Map<String, String> params = new Hashtable<String, String>();
//
//            params.put("image", image);
//            return params;
//        }
//    };
//    {
//        int socketTimeout = 30000;
//        RetryPolicy policy = new DefaultRetryPolicy(socketTimeout, DefaultRetryPolicy.DEFAULT_MAX_RETRIES, DefaultRetryPolicy.DEFAULT_BACKOFF_MULT);
//        stringRequest.setRetryPolicy(policy);
//        RequestQueue requestQueue = Volley.newRequestQueue(this);
//        requestQueue.add(stringRequest);
//    }
//}
//    @Override
//    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
//        super.onActivityResult(requestCode, resultCode, data);
//        if (requestCode == 1 && resultCode == RESULT_OK && data != null && data.getData() != null) {
//            Uri filePath = data.getData();
//            try {
//                Bitmap bitmap = MediaStore.Images.Media.getBitmap(getContentResolver(), filePath);
//                Bitmap lastBitmap = null;
//                lastBitmap = bitmap;
//                //encoding image to string
//                String image = getStringImage(lastBitmap);
//                Log.d("image",image);
//                //passing the image to volley
//                SendImage(image);
//
//            } catch (IOException e) {
//                e.printStackTrace();
//            }
//        }
//    }
//
//
//
//
//    private void getData(){
//        String url="https://attent777.herokuapp.com/hello";
//        final List<String> jsonResponses = new ArrayList<>();
//
//        RequestQueue requestQueue = Volley.newRequestQueue(this);
//        JsonObjectRequest jsonObjectRequest=new JsonObjectRequest(Request.Method.GET, url, null, new Response.Listener<JSONObject>() {
//            @Override
//            public void onResponse(JSONObject response) {
//                try{
//                    JSONObject jsonObject=new JSONObject(response.toString());
//                    Toast.makeText(MainActivity.this, jsonObject.getString("hello"), Toast.LENGTH_SHORT).show();
//
//                }
//                catch (JSONException e)
//                {
//                    e.printStackTrace();
//                }
//            }
//        }, new Response.ErrorListener() {
//            @Override
//            public void onErrorResponse(VolleyError error) {
//
//                Toast.makeText(MainActivity.this, "Please check your internet connection and restart the app", Toast.LENGTH_SHORT).show();
//            }
//        });
//        requestQueue.add(jsonObjectRequest);
//    }
//    private void uploadImage() {
////        File file = new File(filePath);
////
////        Retrofit retrofit = NetworkClient.getRetrofit();
////
////        RequestBody requestBody = RequestBody.create(MediaType.parse("image/*"), file);
////        MultipartBody.Part parts = MultipartBody.Part.createFormData("newimage", file.getName(), requestBody);
////
////        RequestBody name = RequestBody.create(MediaType.parse("text/plain"), "Jeff Bezos");
////        RequestBody uniqueId=RequestBody.create(MediaType.parse("text/plain"),"jb123");
////        UploadApis uploadApis = retrofit.create(UploadApis.class);
////        Call call = uploadApis.uploadImage();
////        call.enqueue(new Callback() {
////            @Override
////            public void onResponse(Call call, Response response) {
////                Toast.makeText(getApplicationContext(),"Done",Toast.LENGTH_LONG).show();
////
////            }
////
////            @Override
////            public void onFailure(Call call, Throwable t) {
////
////            }
////        });
//    }
//}
