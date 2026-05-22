#version 330 core

in vec3 position;
in vec2 texture_coord;
in vec3 normal;
out vec2 out_texture;
out vec3 out_normal;
out vec3 out_fragPos;
		
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;        

void main(){
	vec4 worldPosition = model * vec4(position,1.0);
	gl_Position = projection * view * worldPosition;
	out_texture = vec2(texture_coord);
	out_fragPos = vec3(worldPosition);
	out_normal = mat3(transpose(inverse(model))) * normal;
}
