from conans import CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os


class OpenALConan(ConanFile):
    name = "openal"
    description = "OpenAL Soft is a software implementation of the OpenAL 3D audio API."
    topics = ("conan", "openal", "audio", "api")
    url = "http://github.com/bincrafters/conan-openal"
    homepage = "https://www.openal.org"
    license = "MIT"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    version = "1.19.1"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}

    _source_subfolder = "source_subfolder"

    def configure(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        pass

    def source(self):
        git = tools.Git(folder=self._source_subfolder)
        git.clone("https://github.com/kcat/openal-soft.git", "openal-soft-1.19.1")

    def _platform_defs(self):
        if self.settings.os == "Windows":
            return {
                'ALSOFT_BACKEND_WASAPI': False,
                'ALSOFT_BACKEND_WAVE': False,
                'ALSOFT_BACKEND_WINMM': False,
                'ALSOFT_NO_CONFIG_UTIL': True,
                'ALSOFT_REQUIRE_DSOUND': True,
            }
        if self.settings.os == "Linux":
            return {
                'ALSOFT_BACKEND_SNDIO': False,
                'ALSOFT_BACKEND_WAVE': False,
                'ALSOFT_BACKEND_SDL2': False,
                'ALSOFT_REQUIRE_ALSA': True,
                'ALSOFT_REQUIRE_OSS': True,
                'ALSOFT_REQUIRE_PULSEAUDIO': True,
            }
        if self.settings.os == "Macos":
            return {
                'ALSOFT_BACKEND_WAVE': False,
                'ALSOFT_BACKEND_SDL2': False,
                'ALSOFT_NO_CONFIG_UTIL': True,
                'ALSOFT_REQUIRE_COREAUDIO': True,
            }
        raise ConanInvalidConfiguration('Unsupported OS')

    def _configure_cmake(self):
        cmake = CMake(self)
        return cmake

    def build(self):
        # Need to run within VC environment, or DirectSound will not be found
        with tools.vcvars(self.settings):
            cmake = self._configure_cmake()
            defs = self._platform_defs()
            defs.update({
                'LIBTYPE': 'SHARED' if self.options.shared else 'STATIC',
                'ALSOFT_UTILS': False,
                'ALSOFT_EXAMPLES': False,
                'ALSOFT_TESTS': False,
                'CMAKE_DISABLE_FIND_PACKAGE_SoundIO': True
            })
            cmake.configure(defs=defs)
            cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        self.copy("*COPYING", dst="licenses", keep_path=False, ignore_case=True)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["OpenAL32", 'winmm', 'OLE32', 'Shell32']
        else:
            self.cpp_info.libs = ["openal"]
        if self.settings.os == 'Linux':
            self.cpp_info.libs.extend(['dl', 'm'])
        elif self.settings.os == 'Macos':
            self.cpp_info.frameworks.extend(['AudioToolbox', 'CoreAudio'])
        self.cpp_info.includedirs = ["include", "include/AL"]
        if not self.options.shared:
            self.cpp_info.defines.append('AL_LIBTYPE_STATIC')
