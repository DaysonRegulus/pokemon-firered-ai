/****************************************************************************
** Meta object code from reading C++ file 'EmulatorController.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.15.3)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../../EmulatorController.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'EmulatorController.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.15.3. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_EmulatorController_t {
    QByteArrayData data[38];
    char stringdata0[435];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_EmulatorController_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_EmulatorController_t qt_meta_stringdata_EmulatorController = {
    {
QT_MOC_LITERAL(0, 0, 18), // "EmulatorController"
QT_MOC_LITERAL(1, 19, 7), // "started"
QT_MOC_LITERAL(2, 27, 0), // ""
QT_MOC_LITERAL(3, 28, 12), // "pauseChanged"
QT_MOC_LITERAL(4, 41, 14), // "frameAvailable"
QT_MOC_LITERAL(5, 56, 11), // "dataUpdated"
QT_MOC_LITERAL(6, 68, 13), // "searchUpdated"
QT_MOC_LITERAL(7, 82, 12), // "movieStopped"
QT_MOC_LITERAL(8, 95, 11), // "gameChanged"
QT_MOC_LITERAL(9, 107, 4), // "path"
QT_MOC_LITERAL(10, 112, 5), // "start"
QT_MOC_LITERAL(11, 118, 4), // "stop"
QT_MOC_LITERAL(12, 123, 8), // "schedule"
QT_MOC_LITERAL(13, 132, 4), // "step"
QT_MOC_LITERAL(14, 137, 14), // "setFastForward"
QT_MOC_LITERAL(15, 152, 9), // "setPaused"
QT_MOC_LITERAL(16, 162, 9), // "stopMovie"
QT_MOC_LITERAL(17, 172, 15), // "setDataManifest"
QT_MOC_LITERAL(18, 188, 19), // "setScenarioManifest"
QT_MOC_LITERAL(19, 208, 13), // "setSearchFile"
QT_MOC_LITERAL(20, 222, 16), // "variablesUpdated"
QT_MOC_LITERAL(21, 239, 15), // "scenarioUpdated"
QT_MOC_LITERAL(22, 255, 15), // "searchesUpdated"
QT_MOC_LITERAL(23, 271, 20), // "setAutosaveVariables"
QT_MOC_LITERAL(24, 292, 19), // "setAutosaveScenario"
QT_MOC_LITERAL(25, 312, 19), // "setAutosaveSearches"
QT_MOC_LITERAL(26, 332, 8), // "addCheat"
QT_MOC_LITERAL(27, 341, 4), // "name"
QT_MOC_LITERAL(28, 346, 5), // "value"
QT_MOC_LITERAL(29, 352, 7), // "enabled"
QT_MOC_LITERAL(30, 360, 5), // "Cheat"
QT_MOC_LITERAL(31, 366, 5), // "cheat"
QT_MOC_LITERAL(32, 372, 11), // "enableCheat"
QT_MOC_LITERAL(33, 384, 5), // "index"
QT_MOC_LITERAL(34, 390, 11), // "removeCheat"
QT_MOC_LITERAL(35, 402, 11), // "clearCheats"
QT_MOC_LITERAL(36, 414, 7), // "runOnce"
QT_MOC_LITERAL(37, 422, 12) // "reloadCheats"

    },
    "EmulatorController\0started\0\0pauseChanged\0"
    "frameAvailable\0dataUpdated\0searchUpdated\0"
    "movieStopped\0gameChanged\0path\0start\0"
    "stop\0schedule\0step\0setFastForward\0"
    "setPaused\0stopMovie\0setDataManifest\0"
    "setScenarioManifest\0setSearchFile\0"
    "variablesUpdated\0scenarioUpdated\0"
    "searchesUpdated\0setAutosaveVariables\0"
    "setAutosaveScenario\0setAutosaveSearches\0"
    "addCheat\0name\0value\0enabled\0Cheat\0"
    "cheat\0enableCheat\0index\0removeCheat\0"
    "clearCheats\0runOnce\0reloadCheats"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_EmulatorController[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
      32,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       7,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    0,  174,    2, 0x06 /* Public */,
       3,    1,  175,    2, 0x06 /* Public */,
       4,    1,  178,    2, 0x06 /* Public */,
       5,    0,  181,    2, 0x06 /* Public */,
       6,    0,  182,    2, 0x06 /* Public */,
       7,    0,  183,    2, 0x06 /* Public */,
       8,    1,  184,    2, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
      10,    0,  187,    2, 0x0a /* Public */,
      11,    0,  188,    2, 0x0a /* Public */,
      12,    0,  189,    2, 0x0a /* Public */,
      13,    0,  190,    2, 0x0a /* Public */,
      14,    1,  191,    2, 0x0a /* Public */,
      15,    1,  194,    2, 0x0a /* Public */,
      16,    0,  197,    2, 0x0a /* Public */,
      17,    1,  198,    2, 0x0a /* Public */,
      18,    1,  201,    2, 0x0a /* Public */,
      19,    1,  204,    2, 0x0a /* Public */,
      20,    0,  207,    2, 0x0a /* Public */,
      21,    0,  208,    2, 0x0a /* Public */,
      22,    0,  209,    2, 0x0a /* Public */,
      23,    1,  210,    2, 0x0a /* Public */,
      24,    1,  213,    2, 0x0a /* Public */,
      25,    1,  216,    2, 0x0a /* Public */,
      26,    3,  219,    2, 0x0a /* Public */,
      26,    2,  226,    2, 0x2a /* Public | MethodCloned */,
      26,    1,  231,    2, 0x0a /* Public */,
      32,    2,  234,    2, 0x0a /* Public */,
      32,    1,  239,    2, 0x2a /* Public | MethodCloned */,
      34,    1,  242,    2, 0x0a /* Public */,
      35,    0,  245,    2, 0x0a /* Public */,
      36,    0,  246,    2, 0x08 /* Private */,
      37,    0,  247,    2, 0x08 /* Private */,

 // signals: parameters
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void, QMetaType::QImage,    2,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    9,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString,    2,
    QMetaType::Void, QMetaType::QString,    2,
    QMetaType::Void, QMetaType::QString,    2,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void, QMetaType::Bool,    2,
    QMetaType::Void, QMetaType::QString, QMetaType::QString, QMetaType::Bool,   27,   28,   29,
    QMetaType::Void, QMetaType::QString, QMetaType::QString,   27,   28,
    QMetaType::Void, 0x80000000 | 30,   31,
    QMetaType::Void, QMetaType::UInt, QMetaType::Bool,   33,   29,
    QMetaType::Void, QMetaType::UInt,   33,
    QMetaType::Void, QMetaType::UInt,   33,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

void EmulatorController::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<EmulatorController *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->started(); break;
        case 1: _t->pauseChanged((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 2: _t->frameAvailable((*reinterpret_cast< const QImage(*)>(_a[1]))); break;
        case 3: _t->dataUpdated(); break;
        case 4: _t->searchUpdated(); break;
        case 5: _t->movieStopped(); break;
        case 6: _t->gameChanged((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 7: _t->start(); break;
        case 8: _t->stop(); break;
        case 9: _t->schedule(); break;
        case 10: _t->step(); break;
        case 11: _t->setFastForward((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 12: _t->setPaused((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 13: _t->stopMovie(); break;
        case 14: _t->setDataManifest((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 15: _t->setScenarioManifest((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 16: _t->setSearchFile((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 17: _t->variablesUpdated(); break;
        case 18: _t->scenarioUpdated(); break;
        case 19: _t->searchesUpdated(); break;
        case 20: _t->setAutosaveVariables((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 21: _t->setAutosaveScenario((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 22: _t->setAutosaveSearches((*reinterpret_cast< bool(*)>(_a[1]))); break;
        case 23: _t->addCheat((*reinterpret_cast< const QString(*)>(_a[1])),(*reinterpret_cast< const QString(*)>(_a[2])),(*reinterpret_cast< bool(*)>(_a[3]))); break;
        case 24: _t->addCheat((*reinterpret_cast< const QString(*)>(_a[1])),(*reinterpret_cast< const QString(*)>(_a[2]))); break;
        case 25: _t->addCheat((*reinterpret_cast< const Cheat(*)>(_a[1]))); break;
        case 26: _t->enableCheat((*reinterpret_cast< uint(*)>(_a[1])),(*reinterpret_cast< bool(*)>(_a[2]))); break;
        case 27: _t->enableCheat((*reinterpret_cast< uint(*)>(_a[1]))); break;
        case 28: _t->removeCheat((*reinterpret_cast< uint(*)>(_a[1]))); break;
        case 29: _t->clearCheats(); break;
        case 30: _t->runOnce(); break;
        case 31: _t->reloadCheats(); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        {
            using _t = void (EmulatorController::*)();
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::started)) {
                *result = 0;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)(bool );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::pauseChanged)) {
                *result = 1;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)(const QImage & );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::frameAvailable)) {
                *result = 2;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)();
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::dataUpdated)) {
                *result = 3;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)();
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::searchUpdated)) {
                *result = 4;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)();
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::movieStopped)) {
                *result = 5;
                return;
            }
        }
        {
            using _t = void (EmulatorController::*)(const QString & );
            if (*reinterpret_cast<_t *>(_a[1]) == static_cast<_t>(&EmulatorController::gameChanged)) {
                *result = 6;
                return;
            }
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject EmulatorController::staticMetaObject = { {
    QMetaObject::SuperData::link<QObject::staticMetaObject>(),
    qt_meta_stringdata_EmulatorController.data,
    qt_meta_data_EmulatorController,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *EmulatorController::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *EmulatorController::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_EmulatorController.stringdata0))
        return static_cast<void*>(this);
    return QObject::qt_metacast(_clname);
}

int EmulatorController::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 32)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 32;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 32)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 32;
    }
    return _id;
}

// SIGNAL 0
void EmulatorController::started()
{
    QMetaObject::activate(this, &staticMetaObject, 0, nullptr);
}

// SIGNAL 1
void EmulatorController::pauseChanged(bool _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 1, _a);
}

// SIGNAL 2
void EmulatorController::frameAvailable(const QImage & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 2, _a);
}

// SIGNAL 3
void EmulatorController::dataUpdated()
{
    QMetaObject::activate(this, &staticMetaObject, 3, nullptr);
}

// SIGNAL 4
void EmulatorController::searchUpdated()
{
    QMetaObject::activate(this, &staticMetaObject, 4, nullptr);
}

// SIGNAL 5
void EmulatorController::movieStopped()
{
    QMetaObject::activate(this, &staticMetaObject, 5, nullptr);
}

// SIGNAL 6
void EmulatorController::gameChanged(const QString & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(std::addressof(_t1))) };
    QMetaObject::activate(this, &staticMetaObject, 6, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
