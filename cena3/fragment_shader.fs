#version 330 core

// parametros da iluminacao ambiente e difusa
uniform vec3 lightPos1; // define coordenadas de posicao da luz #1
uniform vec3 lightPos2; 
uniform float ka; // coeficiente de reflexao ambiente
uniform float kd; // coeficiente de reflexao difusa

// parametros da iluminacao especular
uniform vec3 viewPos; // define coordenadas com a posicao da camera/observador
uniform float ks; // coeficiente de reflexao especular
uniform float ns; // expoente de reflexao especular
uniform bool useInternalLights; // limita as luzes internas aos objetos internos
uniform bool isLightSource; // desenha a propria fonte de luz sem sombrear

// parametro com a cor da(s) fonte(s) de iluminacao
vec3 lightColor1 = vec3(1.0, 0.82, 0.45);
vec3 lightColor2 = vec3(1.0, 0.25, 0.65);

uniform bool ambientOn;
uniform bool light1On;
uniform bool light2On;

uniform float ambientIntensity;
uniform float diffuseFactor;
uniform float specularFactor;
float light2Intensity = 3.0;
float light1Intensity = 1.5;
// parametros recebidos do vertex shader
in vec3 out_normal; // recebido do vertex shader
in vec3 out_fragPos; // recebido do vertex shader


uniform vec4 color;
in vec2 out_texture;
uniform sampler2D imagem;
out vec4 FragColor;

vec3 ambientColor = vec3(1.0, 1.0, 1.0);

void main(){
	vec4 texColor = texture(imagem, out_texture);

	if (isLightSource) {
		FragColor = texColor;
		return;
	}

	// calculando reflexao ambiente
	float atual_light = ambientIntensity;

	if(!ambientOn){
		atual_light = 0.0;
	}

	// ambient should not affect objects inside the interior scope
	vec3 ambient = vec3(0.0);
	if (!useInternalLights) {
		ambient = ka * vec3(1.0,1.0,1.0) * atual_light;
	}
	vec3 lighting = ambient;

	if (useInternalLights && light1On) {//so incrementa se a luz tiver acesa e se o objeto estiver no interior
		//luz 1 -> luminaria 
		
		// calculando reflexao difusa
		vec3 norm1 = normalize(out_normal); // normaliza vetores perpendiculares
		vec3 lightDir1 = normalize(lightPos1 - out_fragPos); // direcao da luz
		float diff1 = max(dot(norm1, lightDir1), 0.0); // verifica limite angular (entre 0 e 90)
		float distance1 = length(lightPos1 - out_fragPos);
		float attenuation1 = 1.0 / (1.0 + 0.08 * distance1 + 0.025 * distance1 * distance1);
		vec3 diffuse1 = light1Intensity * diffuseFactor * kd * diff1 * lightColor1 * attenuation1; // iluminacao difusa
		
		// calculando reflexao especular
		vec3 viewDir1 = normalize(viewPos - out_fragPos); // direcao do observador/camera
		vec3 reflectDir1 = reflect(-lightDir1, norm1); // direcao da reflexao
		float spec1 = pow(max(dot(viewDir1, reflectDir1), 0.0), ns);
		vec3 specular1 = light1Intensity * specularFactor * ks * spec1 * lightColor1 * attenuation1;
		lighting += diffuse1 + specular1;
	}

	if(useInternalLights && light2On){//so incrementa se a luz tiver acesa e se o objeto estiver no interior

		//fazendo o mesmo pra fonte de luz 2 - desenho 
		vec3 norm2 = normalize(out_normal); // normaliza vetores perpendiculares
		vec3 lightDir2 = normalize(lightPos2 - out_fragPos); // direcao da luz
		float diff2 = max(dot(norm2, lightDir2), 0.0); // verifica limite angular (entre 0 e 90)
		float distance2 = length(lightPos2 - out_fragPos);
		float attenuation2 = 1.0 / (1.0 + 0.08 * distance2 + 0.025 * distance2 * distance2);
		vec3 diffuse2 = light2Intensity * diffuseFactor * kd * diff2 * lightColor2 * attenuation2; // iluminacao difusa
		
		// calculando reflexao especular
		vec3 viewDir2 = normalize(viewPos - out_fragPos); // direcao do observador/camera
		vec3 reflectDir2 = reflect(-lightDir2, norm2); // direcao da reflexao
		float spec2 = pow(max(dot(viewDir2, reflectDir2), 0.0), ns);
		vec3 specular2 = light2Intensity * specularFactor * ks * spec2 * lightColor2 * attenuation2;
		lighting += diffuse2 + specular2;
	}
	
	// aplicando o modelo de iluminacao
	vec4 result = vec4(lighting,1.0) * texColor; // aplica iluminacao

	FragColor = result;
	
}
