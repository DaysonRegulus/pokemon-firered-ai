/****************************************************************************
** Meta object code from reading C++ file 'MainWindow.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.15.3)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../../MainWindow.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'MainWindow.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.15.3. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_MainWindow_t {
    QByteArrayData data[23];
    char stringdata0[252];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_MainWindow_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_MainWindow_t qt_meta_stringdata_MainWindow = {
    {
QT_MOC_LITERAL(0, 0, 10), // "MainWindow"
QT_MOC_LITERAL(1, 11, 7), // "openAny"
QT_MOC_LITERAL(2, 19, 0), // ""
QT_MOC_LITERAL(3, 20, 9), // "loadState"
QT_MOC_LITERAL(4, 30, 14), // "updateScenario"
QT_MOC_LITERAL(5, 45, 13), // "resetScenario"
QT_MOC_LITERAL(6, 59, 13), // "performSearch"
QT_MOC_LITERAL(7, 73, 19), // "updateSearchResults"
QT_MOC_LITERAL(8, 93, 11), // "QModelIndex"
QT_MOC_LITERAL(9, 105, 12), // "removeSearch"
QT_MOC_LITERAL(10, 118, 13), // "migrateSearch"
QT_MOC_LITERAL(11, 132, 11), // "addVariable"
QT_MOC_LITERAL(12, 144, 14), // "removeVariable"
QT_MOC_LITERAL(13, 159, 8), // "addCheat"
QT_MOC_LITERAL(14, 168, 11), // "removeCheat"
QT_MOC_LITERAL(15, 180, 9), // "integrate"
QT_MOC_LITERAL(16, 190, 6), // "before"
QT_MOC_LITERAL(17, 197, 5), // "after"
QT_MOC_LITERAL(18, 203, 9), // "extension"
QT_MOC_LITERAL(19, 213, 9), // "startGame"
QT_MOC_LITERAL(20, 223, 4), // "path"
QT_MOC_LITERAL(21, 228, 10), // "changeGame"
QT_MOC_LITERAL(22, 239, 12) // "startEpisode"

    },
    "MainWindow\0openAny\0\0loadState\0"
    "updateScenario\0resetScenario\0performSearch\0"
    "updateSearchResults\0QModelIndex\0"
    "removeSearch\0migrateSearch\0addVariable\0"
    "removeVariable\0addCheat\0removeCheat\0"
    "integrate\0before\0after\0extension\0"
    "startGame\0path\0changeGame\0startEpisode"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_MainWindow[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
      16,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    1,   94,    2, 0x0a /* Public */,
       3,    1,   97,    2, 0x0a /* Public */,
       4,    0,  100,    2, 0x08 /* Private */,
       5,    0,  101,    2, 0x08 /* Private */,
       6,    0,  102,    2, 0x08 /* Private */,
       7,    1,  103,    2, 0x08 /* Private */,
       9,    0,  106,    2, 0x08 /* Private */,
      10,    0,  107,    2, 0x08 /* Private */,
      11,    0,  108,    2, 0x08 /* Private */,
      12,    0,  109,    2, 0x08 /* Private */,
      13,    0,  110,    2, 0x08 /* Private */,
      14,    0,  111,    2, 0x08 /* Private */,
      15,    3,  112,    2, 0x08 /* Private */,
      19,    1,  119,    2, 0x08 /* Private */,
      21,    1,  122,    2, 0x08 /* Private */,
      22,    0,  125,    2, 0x08 /* Private */,

 // slots: parameters
    QMetaType::Void, QMetaType::QString,    2,
    QMetaType::Void, QMetaType::QString,    2,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, 0x80000000 | 8,    2,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QString, QMetaType::QString, QMetaType::QString,   16,   17,   18,
    QMetaType::Void, QMetaType::QString,   20,
    QMetaType::Void, QMetaType::QString,   20,
    QMetaType::Void,

       0        // eod
};

void MainWindow::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<MainWindow *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->openAny((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 1: _t->loadState((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 2: _t->updateScenario(); break;
        case 3: _t->resetScenario(); break;
        case 4: _t->performSearch(); break;
        case 5: _t->updateSearchResults((*reinterpret_cast< const QModelIndex(*)>(_a[1]))); break;
        case 6: _t->removeSearch(); break;
        case 7: _t->migrateSearch(); break;
        case 8: _t->addVariable(); break;
        case 9: _t->removeVariable(); break;
        case 10: _t->addCheat(); break;
        case 11: _t->removeCheat(); break;
        case 12: _t->integrate((*reinterpret_cast< const QString(*)>(_a[1])),(*reinterpret_cast< const QString(*)>(_a[2])),(*reinterpret_cast< const QString(*)>(_a[3]))); break;
        case 13: _t->startGame((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 14: _t->changeGame((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 15: _t->startEpisode(); break;
        default: ;
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject MainWindow::staticMetaObject = { {
    QMetaObject::SuperData::link<QMainWindow::staticMetaObject>(),
    qt_meta_stringdata_MainWindow.data,
    qt_meta_data_MainWindow,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *MainWindow::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *MainWindow::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_MainWindow.stringdata0))
        return static_cast<void*>(this);
    return QMainWindow::qt_metacast(_clname);
}

int MainWindow::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QMainWindow::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 16)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 16;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 16)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 16;
    }
    return _id;
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
