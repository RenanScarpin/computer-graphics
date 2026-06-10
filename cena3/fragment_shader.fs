#version 330 core

// ambient and diffuse lighting parameters
uniform vec3 lightPos1; // light #1 - lamp (indoor)
uniform vec3 lightPos2; // light #2 - drawing (indoor)
uniform vec3 lightPos3; // light #3 - street lamp (outdoor)
uniform vec3 lightPos4; // light #4 - car left headlight (outdoor)
uniform vec3 lightPos5; // light #5 - car right headlight (outdoor)
uniform float ka; // ambient reflection coefficient
uniform float kd; // diffuse reflection coefficient

// specular lighting parameters
uniform vec3 viewPos; // provides coordinates of the camera/observer position
uniform float ks; // specular reflection coefficient
uniform float ns; // specular reflection exponent
uniform bool isLightSource; // draws the light source itself without shading

// object's lighting profile: how it responds to diffuse/specular reflection
uniform float objDiffuse;
uniform float objSpecular;

// true when the camera is inside the environment: turns on internal lights and
// turns off external ones; false does the opposite
uniform bool cameraInside;

// parameter with the color of the light source(s)
vec3 lightColor1 = vec3(1.0, 0.82, 0.45);
vec3 lightColor2 = vec3(1.0, 0.25, 0.65);
vec3 lightColor3 = vec3(1.0, 0.90, 0.70); // poste - branco quente
vec3 lightColor4 = vec3(0.90, 0.95, 1.0); // farol - branco frio
vec3 lightColor5 = vec3(0.90, 0.95, 1.0); // farol - branco frio


uniform bool ambientOn;
uniform bool light1On;
uniform bool light2On;
uniform bool light3On;
uniform bool light4On;
uniform bool light5On;

uniform float ambientIntensity;
uniform float diffuseFactor;
uniform float specularFactor;
float light1Intensity = 3.0;
float light2Intensity = 3.0;
float light3Intensity = 3.0;
float light4Intensity = 1.5;
float light5Intensity = 1.5;

// parameters received from the vertex shader
in vec3 out_normal; // received from the vertex shader
in vec3 out_fragPos; // received from the vertex shader


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

	// calculating ambient reflection
	float atual_light = ambientIntensity;

	if(!ambientOn){
		atual_light = 0.0;
	}

	// ambient light affects all objects (indoor and outdoor)
	vec3 ambient = ka * vec3(1.0,1.0,1.0) * atual_light;
	vec3 lighting = ambient;

	// internal lights: only turn on when the camera is inside the environment and the toggle is on
	if (cameraInside && light1On) {
		// light 1 -> lamp

		// calculating diffuse reflection
		vec3 norm1 = normalize(out_normal); // normalizes perpendicular vectors
		vec3 lightDir1 = normalize(lightPos1 - out_fragPos); // light direction
		float diff1 = max(dot(norm1, lightDir1), 0.0); // checks angular limit (between 0 and 90)
		float distance1 = length(lightPos1 - out_fragPos);
		float attenuation1 = 1.0 / (1.0 + 0.08 * distance1 + 0.025 * distance1 * distance1);
		vec3 diffuse1 = light1Intensity * diffuseFactor * objDiffuse * kd * diff1 * lightColor1 * attenuation1; // diffuse lighting

		// calculating specular reflection
		vec3 viewDir1 = normalize(viewPos - out_fragPos); // direction of the observer/camera
		vec3 reflectDir1 = reflect(-lightDir1, norm1); // reflection direction
		float spec1 = pow(max(dot(viewDir1, reflectDir1), 0.0), ns);
		vec3 specular1 = light1Intensity * specularFactor * objSpecular * ks * spec1 * lightColor1 * attenuation1;
		lighting += diffuse1 + specular1;
	}

	if(cameraInside && light2On){
		// doing the same for light source 2 - drawing
		vec3 norm2 = normalize(out_normal); // normalizes perpendicular vectors
		vec3 lightDir2 = normalize(lightPos2 - out_fragPos); // light direction
		float diff2 = max(dot(norm2, lightDir2), 0.0); // checks angular limit (between 0 and 90)
		float distance2 = length(lightPos2 - out_fragPos);
		float attenuation2 = 1.0 / (1.0 + 0.08 * distance2 + 0.025 * distance2 * distance2);
		vec3 diffuse2 = light2Intensity * diffuseFactor * objDiffuse * kd * diff2 * lightColor2 * attenuation2; // diffuse lighting

		// calculating specular reflection
		vec3 viewDir2 = normalize(viewPos - out_fragPos); // direction of the observer/camera
		vec3 reflectDir2 = reflect(-lightDir2, norm2); // reflection direction
		float spec2 = pow(max(dot(viewDir2, reflectDir2), 0.0), ns);
		vec3 specular2 = light2Intensity * specularFactor * objSpecular * ks * spec2 * lightColor2 * attenuation2;
		lighting += diffuse2 + specular2;
	}

	// external lights: only turn on when the camera is outside the environment and the toggle is on
	if(!cameraInside && light3On){
		// light 3 -> street lamp
		vec3 norm3 = normalize(out_normal);
		vec3 lightDir3 = normalize(lightPos3 - out_fragPos);
		float diff3 = max(dot(norm3, lightDir3), 0.0);
		float distance3 = length(lightPos3 - out_fragPos);
		float attenuation3 = 1.0 / (1.0 + 0.08 * distance3 + 0.025 * distance3 * distance3);
		vec3 diffuse3 = light3Intensity * diffuseFactor * objDiffuse * kd * diff3 * lightColor3 * attenuation3;

		vec3 viewDir3 = normalize(viewPos - out_fragPos);
		vec3 reflectDir3 = reflect(-lightDir3, norm3);
		float spec3 = pow(max(dot(viewDir3, reflectDir3), 0.0), ns);
		vec3 specular3 = light3Intensity * specularFactor * objSpecular * ks * spec3 * lightColor3 * attenuation3;
		lighting += diffuse3 + specular3;
	}

	if(!cameraInside && light4On){
		// light 4 -> car left headlight
		vec3 norm4 = normalize(out_normal);
		vec3 lightDir4 = normalize(lightPos4 - out_fragPos);
		float diff4 = max(dot(norm4, lightDir4), 0.0);
		float distance4 = length(lightPos4 - out_fragPos);
		float attenuation4 = 1.0 / (1.0 + 0.08 * distance4 + 0.025 * distance4 * distance4);
		vec3 diffuse4 = light4Intensity * diffuseFactor * objDiffuse * kd * diff4 * lightColor4 * attenuation4;

		vec3 viewDir4 = normalize(viewPos - out_fragPos);
		vec3 reflectDir4 = reflect(-lightDir4, norm4);
		float spec4 = pow(max(dot(viewDir4, reflectDir4), 0.0), ns);
		vec3 specular4 = light4Intensity * specularFactor * objSpecular * ks * spec4 * lightColor4 * attenuation4;
		lighting += diffuse4 + specular4;
	}

	if(!cameraInside && light5On){
		// light 5 -> car right headlight
		vec3 norm5 = normalize(out_normal);
		vec3 lightDir5 = normalize(lightPos5 - out_fragPos);
		float diff5 = max(dot(norm5, lightDir5), 0.0);
		float distance5 = length(lightPos5 - out_fragPos);
		float attenuation5 = 1.0 / (1.0 + 0.08 * distance5 + 0.025 * distance5 * distance5);
		vec3 diffuse5 = light5Intensity * diffuseFactor * objDiffuse * kd * diff5 * lightColor5 * attenuation5;

		vec3 viewDir5 = normalize(viewPos - out_fragPos);
		vec3 reflectDir5 = reflect(-lightDir5, norm5);
		float spec5 = pow(max(dot(viewDir5, reflectDir5), 0.0), ns);
		vec3 specular5 = light5Intensity * specularFactor * objSpecular * ks * spec5 * lightColor5 * attenuation5;
		lighting += diffuse5 + specular5;
	}


	// applying the lighting model
	vec4 result = vec4(lighting,1.0) * texColor; // applies lighting

	FragColor = result;

}
