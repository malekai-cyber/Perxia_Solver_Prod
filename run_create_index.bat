@echo off
echo Ejecutando script de creacion de indice...
python create_index_simple.py > index_creation_log.txt 2>&1
echo.
echo Resultados guardados en index_creation_log.txt
type index_creation_log.txt
